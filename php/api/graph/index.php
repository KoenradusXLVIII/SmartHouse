<?php
    // Show errors
    ini_set('display_errors', 1);

   include_once '../config/database.php';
   session_start();
   
   if($_SERVER["REQUEST_METHOD"] == "POST") {
      // username and password sent from form 
      
      // Connect to database
      $database = new Database();
      $db = $database->getConnection();
      
      $myusername = mysqli_real_escape_string($db,$_POST['username']);
      $mypassword = mysqli_real_escape_string($db,$_POST['password']); 
      
      $query = "SELECT id FROM users WHERE name = '$myusername' and pass = '$mypassword'";
      $result = $db->query($query);
      $row = $result->fetch_assoc();

      if($row) {    
        $_SESSION["user_id"] = $row["id"];
        header("location: intraday.php");
      } else {
         $error = "Your username or password is invalid";
      }
    }
?>

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>SensorNode - Login</title>

    <!-- Bootstrap core CSS -->
    <link href="css/bootstrap.min.css" rel="stylesheet">


    <style>
      .bd-placeholder-img {
        font-size: 1.125rem;
        text-anchor: middle;
      }

      @media (min-width: 768px) {
        .bd-placeholder-img-lg {
          font-size: 3.5rem;
        }
      }
    </style>
    <!-- Custom styles for this template -->
    <link href="css/signin.css" rel="stylesheet">
    <link rel="icon" href="favicon.ico" type="image/x-icon" />
  </head>
  <body class="text-center">
    <form class="form-signin" action="" method="post">
      <h1 class="h3 mb-3 font-weight-normal">Please sign in</h1>
      <label for="username" class="sr-only">User name</label>
      <input type="text" name="username" class="form-control" placeholder="User name" required autofocus>
      <label for="password" class="sr-only">Password</label>
      <input type="password" name="password" class="form-control" placeholder="Password" required>
      <div style = "color:#cc0000; margin-top:10px; margin-bottom:10px"><?php echo $error; ?></div>
      <div class="checkbox mb-3">
        <label>
          <input type="checkbox" value="remember-me"> Remember me
        </label>
      </div>
      <button class="btn btn-lg btn-primary btn-block" type="submit">Sign in</button>
      <p class="mt-5 mb-3 text-muted">&copy; Joost Verberk 2018</p>
    </form>
</body>
</html>