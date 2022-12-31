line=$1
echo $line | waybackurls | anew $line/urls.txt;
echo $line | gau --threads 5 | anew $line/urls.txt
echo $line | katana -d 5 silent | anew $line/urls.txt
echo $line | hakrawler | anew $line/urls.txt
cat $line/urls.txt| sed '$!N; /^\(.*\)\n\1$/!P; D'| grep -P '\.php|\.asp|\.js|\.jsp' | anew $line/endpoints.txt
cat $line/urls.txt| grep -Po '(?:\?|\&)(?<key>[\w]+)(?:\=|\&?)(?<value>[\w+,.-]*)' | tr -d '?' | tr -d '&' | anew $line/parameters.txt
