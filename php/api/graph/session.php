<?php
    // Show errors
    ini_set('display_errors', 1);

   include('../config/database.php');
   session_start();
   
   if(!isset($_SESSION['user_id'])){
      header("location:index.php");
   }
?>