# sotareport

This tool will help you generating your radio QSO log for submission to the SOTA Database at \
https://www.sotadata.org.uk/en/upload/activator/csv

It can be used for both Activators and Chasers.

The sotareport SOTA Log Submit Tool
===================================

This tool will append the given log to the output file.

Usage: 

```
./sotareport.py OUTPUTFILE
```


## Example

```
######################################################################
Enter station info:
     Your Callsign: HB3/DO3IC
       Your Summit: HB/AI-013
      Found Summit: Furgglenfirst (1952m), Appenzell Innerrhoden, Switzerland
   Date (DD/MM/YY): 26/06/20
######################################################################
Adding log to 'output.csv'
Enter QSO #1:
 Time (HHMM - UTC): 1215
          Callsign: HB9EAJ/P
  Freq (21MHz/80m): 29MHz
  Mode (CW/SSB/FM): 
        S2S Summit: HB/SO-003
      Found Summit: Röti (1395m), Solothurn, Switzerland
          Distance: 144km
           Comment: 
######################################################################
Enter QSO #2:
 Time (HHMM - UTC): 1220
          Callsign: HB9GUX/p
  Freq (21MHz/80m): 28MHz
  Mode (CW/SSB/FM): SSB
        S2S Summit: HB/GR-294
      Found Summit: Chrüz (2196m), Graubünden, Switzerland
          Distance: 41km
           Comment: 
######################################################################
Enter QSO #3:
 Time (HHMM - UTC): 
Error: Invalid time format - use HHMM or HH:MM 24h UTC
 Time (HHMM - UTC): 1221
          Callsign: EA2DT
  Freq (21MHz/80m): 28MHz
  Mode (CW/SSB/FM): SSB
        S2S Summit: 
           Comment: 
######################################################################
Enter QSO #4:
 Time (HHMM - UTC): 1223
          Callsign: DB7MM
  Freq (21MHz/80m): 28MHz
  Mode (CW/SSB/FM): SSB
        S2S Summit: 
           Comment: 
######################################################################
```
