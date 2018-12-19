#!/usr/bin/perl
use File::Path;
use DBI;

my $path = '/data/graph';
if(-e $path) { rmtree($path); }
mkdir($path);

@arrs = ("")

my $stime = `date +%Y%m%d`; chop($stime); $stime .= '1000';
if( length($stime) != 12 ) { print "Error get date"; exit; }
my $period = 86400;    # 24 hours
my $login = '';   # Zabbix Web User
my $pass = ''; # Zabbix Web User Password, must be URL Encoded
my $cook = "/tmp/cookie";
my $dsn = 'DBI:xxx:xxx:xxx'; # Connect MySQL DB "zabbix" on localhost
my $db_user_name = ''; # MySQL DB user
my $db_password = ''; # MySQL DB user password
my $dbh = DBI->connect($dsn, $db_user_name, $db_password);
my $sth = $dbh->prepare(qq{select a.name,a.hsize,a.vsize, b.resourceid, b.width, b.height,b.x,b.y from screens a,screens_items as b where a.screenid=b.screenid and a.templateid<=>NULL order by a.name});
$sth->execute();
my %screens;

# Get all graphs by using curl

while (my ($name,$hsize,$vsize, $id,$width,$height,$x,$y) = $sth->fetchrow_array())
{
    if(length($id) > 2 && grep /^$name$/,@arrs){
        #print "$id => $ids\n";
        my $p = "$path/$name.$hsize.$vsize.$y.$x.$id.png";
        my $strcomm  = `curl  -c $cook -b $cook -d "request=&name=$login&password=$pass&autologin=1&enter=Sign+in"  localhost/zabbix/index.php`;
        $strcomm  = `curl  -b $cook -F  "graphid=$id" -F "period=$period" -F "stime=$stime" -F "width=$width" -F "height=$height" localhost/zabbix/chart2.php > $p`;
    }
}

exit ;
