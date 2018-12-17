<?php
class Meas{

    // database connection and table name
    private $conn;
    private $table_name = "meas";

    // object properties
    public $id;
    public $timestamp;
    public $value;
    public $sensor_id;

    // constructor with $db as database connection
    public function __construct($db){
        $this->conn = $db;
    }

    // read measurements
    function read(){
        // select all query
        $query = "SELECT meas.timestamp, sensors.name, meas.value, quantities.uom, quantities.name as quantity FROM `meas` LEFT JOIN sensors on meas.sensor_id=sensors.id LEFT JOIN quantities ON sensors.quantity_id=quantities.id";

        // prepare query statement
        $stmt = $this->conn->prepare($query);

        // execute query
        $stmt->execute();
        return $stmt;
    }

    // create product
    function create(){
        // query to insert record
        $query = "INSERT INTO " . $this->table_name . " SET sensor_id=:sensor_id, value=:value";

        // prepare query
        $stmt = $this->conn->prepare($query);

        // sanitize
        $this->sensor_id=htmlspecialchars(strip_tags($this->sensor_id));
        $this->value=htmlspecialchars(strip_tags($this->value));

        // bind values
        $stmt->bindParam(":sensor_id", $this->sensor_id);
        $stmt->bindParam(":value", $this->value);

        // execute query
        if($stmt->execute()){
            return true;
        }

        return false;
    }
}

?>