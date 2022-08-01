<?php 

$host=$_ENV["DB_HOST"];
$db=$_ENV["DB_NAME"];
$user=$_ENV["DB_USER"];
$pass=$_ENV["DB_PASS"];

$con = pg_connect("host=$host dbname=$db user=$user password=$pass")
    or die ("Could not connect to server\n"); 

$query = "SELECT * FROM players"; 

$rs = pg_query($con, $query) or die("Cannot execute query: $query\n");

while ($row = pg_fetch_row($rs)) {
  echo "$row[0] $row[1] $row[2]\n\n";
}

pg_close($con); 

?>