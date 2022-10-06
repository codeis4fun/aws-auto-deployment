#!/bin/bash
MSG="Splitando CSV em arquivos menores de 50000 linhas..."
echo $MSG
awk -v l=50000 '(NR==1){header=$0;next}
                (NR%l==2) {
                   close(file); 
                   file=sprintf("%s.%0.5d.csv",FILENAME,++c)
                   sub(/csv[.]/,"",file)
                   print header > file
                }
                {print > file}' library-collection-inventory.csv