#!/bin/bash

DIRPATH=$1

XMLFILES=$(ls $DIRPATH/*.xml)
for XMLFILE in $XMLFILES; do
    echo $XMLFILE
    xmllint --format $XMLFILE > $XMLFILE.fixed
    mv -f $XMLFILE.fixed $XMLFILE
done
