#!/bin/sh

# Uncomment to have debugging information
# set -x

#-------------------------------------------------------------------------
# Declaration of variables
#-------------------------------------------------------------------------
PVOUTPUTKEY="d1b62a7d17dbebf167b98df9eb2f7c2188438d78"
PVOUTPUTSID="47507"
GROWATTSERIAL="3L36160058"
PVOUTPUTVPV1=NO
PVOUTPUTVPV2=NO
PVCUMFLAG=1
GROWATTMODULEVER=4.0.0.0

#-------------------------------------------------------------------------
# Declaration interfaces and Growatt server destination
#-------------------------------------------------------------------------
DESTINATION=server.growatt.com
INTERFACE=wlan0

#-------------------------------------------------------------------------
# Declaration of script variables
#-------------------------------------------------------------------------
PVOUTPUTURL="http://pvoutput.org/service/r2/addstatus.jsp"
CURLTIMEOUT=60
PVBASEDIR=/home/pi/repository/shell/pvoutput
PVINDIR=$PVBASEDIR/input
PVOUTDIR=$PVBASEDIR/processed
PVLOGDIR=$PVBASEDIR/logs
PVLOGFILE="$PVLOGDIR/growatt_process.log"
PVTMPFILE="$PVBASEDIR/tmp/growattsize"
PVPYTHONFILE="/home/pi/repository/python/pvoutput/input/growatt.csv"
PVCAPFILE="growatt_*.cap"
PVPREFILE="growatt_*.preproc"
LOWERLIMIT=300
DIVIDER="------------------------------------------------------------------------------------"

#-------------------------------------------------------------------------
# Function to accomodate for the changing ip-address of the destination
# server: http://server.growatt.com
#-------------------------------------------------------------------------
destip()
{
	#-------------------------------------------------------------------------
	# Determine the IP address ${DESTIP} from ${DESTINATION} and determine
	# the IP address used in the current iptables rule.
	#-------------------------------------------------------------------------
	DESTIP=$(host ${DESTINATION} | cut -f4 -d' ')
}

#-------------------------------------------------------------------------
# Function to calculate register position based on $OFFSET and parameter.
# There are different Growatt Wifi Module firmware versions.
# The difference between the positions of the position of GROWATTSERIAL
# and the position of the data is +6 positions when 2.0.0.0 firmware or
# 3.0.0.0 firmware is # used (compared to 1.0.0.0 firmware).
#-------------------------------------------------------------------------
calcpos()
{
	case "$GROWATTMODULEVER" in
	"1.0.0.0")
		OFFSETCORRECT=0
	;;
	"2.0.0.0")
		OFFSETCORRECT=6
	;;
	"3.0.0.0")
		OFFSETCORRECT=6
	;;
	"4.0.0.0")
		OFFSETCORRECT=6
	;;
	esac

	echo $(echo $OFFSET + $1 + $OFFSETCORRECT | bc)
}

#-------------------------------------------------------------------------
# Function to check the position of a string in the HEX file
#-------------------------------------------------------------------------
offsetcheck()
{
    echo $(grep -obUaP \
         $(echo -n "$1" | od -A n -t x1 | sed "s/ /\\\x/g") $fn \
         | cut -d ":" -f 1)
}

#-------------------------------------------------------------------------
# Write start of new processing to logfile
#-------------------------------------------------------------------------
echo ${DIVIDER} >> ${PVLOGFILE}
date >> ${PVLOGFILE}
echo ${DIVIDER} >> ${PVLOGFILE}

#-------------------------------------------------------------------------
# Determine if the IP address of growatt.server.com changed
#-------------------------------------------------------------------------
destip

#-------------------------------------------------------------------------
# Capture the Growatt Traffic (stop when 1 packet captured or 5 minutes past)
#-------------------------------------------------------------------------
PID=$(pidof tcpdump)
if [ -n "$PID" ]; then
      kill $PID
      printf "tcpdump killed \n" >> $PVLOGFILE
fi
/usr/sbin/tcpdump -p -i $INTERFACE -nn -G 60 -s 300 -c 1 -w \
                        $PVINDIR/growatt_%Y%m%d_%H:%M.cap \
                        greater 220 and tcp and less 500 and \
                        dst $DESTIP >/dev/null 2>&1

#-------------------------------------------------------------------------
# Remove Growatt data capture files with incorrect length.
# DO NOT remove files with 0 length as they still capture data
# If no capture files are found then write a message in the log and exit.
#-------------------------------------------------------------------------
for fn in $PVINDIR/$PVCAPFILE
do
        #-------------------------------------------------------------------------
        # Determine if files ($PVCAPFILE) exist in the input directory ($PVINDIR)
        #-------------------------------------------------------------------------
	if [ ! -f "$fn" ]; then
                printf "%-50s\n" "No capture in input directory. Processing ended." \
		       >> ${PVLOGFILE}
		exit 0
	else
        	fs=$(stat --format=%s "$fn")
		pd=$(echo $fn | cut -d "_" -f 4)

		# Split capture files in 1 file per packet in $PVTMPFILE and
		# move original capture packet to $PVOUTDIR with .split extension
	  if [ "$fs" -gt $LOWERLIMIT ] && [ "$pd" = "" ]; then
			editcap -c 1 $fn $PVTMPFILE
			mv $fn ${PVOUTDIR}/${fn##*/}.split
               		printf "%-50s : %s\n" \
			       "Capture file split, moved to ${PVOUTDIR##*/} dir." \
		               ${fn##*/}.split >> ${PVLOGFILE}
		fi

		# Move small non-empty files to $PVOUTDIR
		if [ "$fs" -gt 0 -a "$fs" -lt $LOWERLIMIT ]; then
			mv $fn ${PVOUTDIR}/${fn##*/}.smallsize
                	printf "%-50s : %s\n" \
			       "Capture file < ${LOWERLIMIT} chars, moved to ${PVOUTDIR##*/} dir." \
			       ${fn##*/}.smallsize >> ${PVLOGFILE}
		fi
	fi
done

#-------------------------------------------------------------------------
# Preprocess the input files
#-------------------------------------------------------------------------
for fn in $PVTMPFILE*
do
	if [ -f "$fn" ]; then
		fnnew=$(printf "growatt_%s_%s:%s_%s.preproc" \
		      $(echo $fn | cut -d "_" -f 3 | cut -c1-8)   \
		      $(echo $fn | cut -d "_" -f 3 | cut -c9-10)  \
		      $(echo $fn | cut -d "_" -f 3 | cut -c11-12) \
		      $(echo $fn | cut -d "_" -f 3 | cut -c13-14))

		#-------------------------------------------------------------------------
		# Use $GROWATTSERIAL to find the reference point to be used as offset
		#-------------------------------------------------------------------------
		STRING1=$(offsetcheck "Inverter")	# Exclude equal sized packet (no data)
		STRING2=$(offsetcheck "5279")		# Exclude (re)logon packet (portnumber)
		GSERIAL=$(offsetcheck "$GROWATTSERIAL")	# Exclude non-match serial packet

		if [ "$STRING1" = "" ] && [ "$STRING2" = "" ] && [ "$GSERIAL" != "" ] ; then
			mv $fn $PVINDIR/${fnnew##*/}
       	        	printf "%-50s : %s\n" \
		               "Valid file moved to ${PVINDIR##*/} dir." \
			       ${fnnew##*/} >> ${PVLOGFILE}
		else
       	        	printf "%-50s : %s\n" \
			       "Invalid file removed" \
			       ${fn##*/} >> ${PVLOGFILE}
			rm $fn
		fi
	fi
done

#-------------------------------------------------------------------------
# Process valid (already preprocessed) files
#-------------------------------------------------------------------------
for fn in $PVINDIR/$PVPREFILE
do
  #-------------------------------------------------------------------------
  # Determine if files ($PVCAPFILE) exist in the input directory ($PVINDIR)
  #-------------------------------------------------------------------------
	if [ ! -f "$fn" ]; then
  	printf "%-50s\n" "No input files to be processed. Processing ended." \
			>> ${PVLOGFILE}
		exit 0
	fi

  #-------------------------------------------------------------------------
  # Fill the variables for Date (fd) and Time (ft)
  #-------------------------------------------------------------------------
  fd=$(echo $fn | cut -d_ -f2)
  ft=$(echo $fn | cut -d_ -f3 | cut -c1-5)

	#-------------------------------------------------------------------------
	# Use $GROWATTSERIAL to find the reference point to be used as offset
	# Also exclude empty files from processing
	#-------------------------------------------------------------------------
	OFFSET=$(offsetcheck "$GROWATTSERIAL")
  fs=$(stat --format=%s "$fn")

	if [ "$OFFSET" = "" ] && [ $fs -ne 0 ]; then
  	printf "%s;%s;"    $fd $ft   >> ${PVLOGFILE}
  	printf "%6s;%6s;"  "NA" "NA" >> ${PVLOGFILE}
		printf "%-50s : %s\n" "File removed. Serial number ${GROWATTSERIAL} not found" \
			${fn##*/} >> ${PVLOGFILE}
		rm $fn

	elif [ $fs -ne 0 ]; then
    #-------------------------------------------------------------------------
    # Extract Growatt Inverter information
    #-------------------------------------------------------------------------

		# Use E_Total or E_Today depending on the users preference (PVCUMFLAG)
		if [ "$PVCUMFLAG" = 1 ]; then
			# E_Total (Wh) - pvoutput -> Energy (v1) if c1=1
        		ETt=$(hexdump -C -s $(calcpos 71) -n 4 $fn \
			     | cut -c11-21 | tr a-f A-F | sed "s/ //g")
        		ET=$(echo "ibase=16;obase=A;scale=2;$ETt*64" | bc)
			PVENERGY=$ET
		else
			# E_Today(Wh)  - pvoutput -> Energy (v1) if c1=0
			ETdt=$(hexdump -C -s $(calcpos 67) -n 4 $fn \
			     | cut -c11-21 | tr a-f A-F | sed "s/ //g")
			ETd=$(echo "ibase=16;obase=A;scale=2;$ETdt*64" | bc)
			PVCUMFLAG=0
			PVENERGY=$ETd
		fi

		# Pac(W)        - pvoutput -> Power (v2)
		Pact=$(hexdump -C -s $(calcpos 37) -n 4 $fn \
		     | cut -c11-21 | tr a-f A-F | sed "s/ //g")
		Pac=$(echo "ibase=16;obase=A;scale=1;$Pact/A" | bc)

		# Vpv1(V)
		if [ "$PVOUTPUTVPV1" = "YES" ]; then
			Vpv1t=$(hexdump -C -s $(calcpos 21) -n 2 $fn \
			      | cut -c11-15 | tr a-f A-F | sed "s/ //g")
			Vpv1=$(echo "ibase=16;obase=A;scale=1;$Vpv1t/A" | bc)
		fi

		# Tmp(C)
		Tmpt=$(hexdump -C -s $(calcpos 79) -n 2 $fn | cut -c11-15 | tr a-f A-F | sed "s/ //g")
		Tmp=$(echo "ibase=16;obase=A;scale=1;$Tmpt/A" | bc)

    #-------------------------------------------------------------------------
    # Write the details per record to the logfile
    #-------------------------------------------------------------------------
    printf "%s;%s;"      $fd       $ft  >> ${PVLOGFILE}
    printf "%10u;%7.1f;" $PVENERGY $Pac >> ${PVLOGFILE}
		printf "%7.1f;"      $Vpv1          >> ${PVLOGFILE}
		printf "%6.1f;"      $Tmp           >> ${PVLOGFILE}

		#-------------------------------------------------------------------------
    # Write the details to the python transferfile
    #-------------------------------------------------------------------------
		printf "Energy PV,Power PV\n" > ${PVPYTHONFILE}
    printf "%s,%s\n" $PVENERGY $Pac >> ${PVPYTHONFILE}

		#-------------------------------------------------------------------------
    # Process PVOutput
    #-------------------------------------------------------------------------
		PVOutput="$(python /home/pi/repository/python/pvoutput/process.py growatt)"

		#-------------------------------------------------------------------------
		# Process input files
		#-------------------------------------------------------------------------
		mv $fn ${PVOUTDIR}/${fn##*/}.ok
   	printf "%-50s : %s\n" \
 			"Processed file, moved to ${PVOUTDIR##*/} dir." \
    ${fn##*/}.ok >> ${PVLOGFILE}

    #-------------------------------------------------------------------------
    # Submit the data to pvoutput.org servers and capture the result
    #-------------------------------------------------------------------------

		# if [ "$PVOUTPUTVPV1" = "YES" ] && [ "$PVOUTPUTVPV2" = "YES" ]; then
		#
		# 	result=$(curl -s -S --max-time $CURLTIMEOUT \
		# 		-d "d=$fd"    -d "t=$ft"    -d "v1=$PVENERGY" -d "v2=$Pac" \
		# 		-d "v6=$Vpv1" -d "v7=$Vpv2" \
		# 		-d "c1=$PVCUMFLAG" \
		# 		-H "X-Pvoutput-Apikey: $PVOUTPUTKEY" \
		# 		-H "X-Pvoutput-SystemId: $PVOUTPUTSID" $PVOUTPUTURL 2>&1)
		#
		# elif [ "$PVOUTPUTVPV1" = "YES" ] && [ "$PVOUTPUTVPV2" != "YES" ]; then
		#
		# 	result=$(curl -s -S --max-time $CURLTIMEOUT \
		# 		-d "d=$fd"    -d "t=$ft"    -d "v1=$PVENERGY" -d "v2=$Pac" \
		# 		-d "v6=$Vpv1"  \
		# 		-d "c1=$PVCUMFLAG" \
		# 		-H "X-Pvoutput-Apikey: $PVOUTPUTKEY" \
		# 		-H "X-Pvoutput-SystemId: $PVOUTPUTSID" $PVOUTPUTURL 2>&1)
		#
		# elif [ "$PVOUTPUTVPV1" != "YES" ]; then
		#
		# 	result=$(curl -s -S --max-time $CURLTIMEOUT \
		# 		-d "d=$fd" -d "t=$ft" -d "v1=$PVENERGY" -d "v2=$Pac" \
		# 		-d "c1=$PVCUMFLAG" \
		# 		-H "X-Pvoutput-Apikey: $PVOUTPUTKEY" \
		# 		-H "X-Pvoutput-SystemId: $PVOUTPUTSID" $PVOUTPUTURL 2>&1)
		# fi
		#
    # echo $result >> ${PVLOGFILE}
		#
    # #-------------------------------------------------------------------------
    # # Verify succesful upload and archive the files to processed directory
    # #-------------------------------------------------------------------------
    # rescode200=$(echo $result | grep "OK 200: Added Status" | wc -l)
    # rescode400=$(echo $result | grep "Bad request 400" | wc -l)
    # rescode403=$(echo $result | grep "Forbidden 403: Exceeded" | wc -l)
		#
		# # To many uploads within one hour
    # if [ "$rescode403" -eq 1 ]; then
    #   exit 1
    # fi
		#
		# # Upload failed
    # if [ "$rescode400" -eq 1 ]; then
  	# 	mv $fn ${PVOUTDIR}/${fn##*/}.badupload
    # fi
		#
		# # Upload succeeded
    # if [ "$rescode200" -eq 1 ]; then
    # 	mv $fn ${PVOUTDIR}/${fn##*/}.ok
   	# 		printf "%-50s : %s\n" \
 		# 			"Processed file, moved to ${PVOUTDIR##*/} dir." \
    #    	${fn##*/}.ok >> ${PVLOGFILE}
    # fi

    #-------------------------------------------------------------------------
		# Reset the global variables for the next run
    #-------------------------------------------------------------------------
    #result=""
    #rescode200=0
    #rescode400=0
    #rescode403=0
	fi
done
