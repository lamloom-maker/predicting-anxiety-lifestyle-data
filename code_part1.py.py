DATA Revenues;
   INPUT Year Total_Revenues;
   DATALINES;
   1990 4
   1991 5
   1992 7
   1993 6
   1994 8
   1995 9
   1996 5
   1997 2
   1998 3.5
   1999 5.5
   2000 6.5
;
RUN;


PROC PRINT DATA=Revenues;
   TITLE 'Imported Dataset - Revenues';
RUN;


PROC MEANS DATA=Revenues N MEAN MEDIAN MIN MAX STD;
   TITLE 'Descriptive Statistics for Total Revenues';
RUN;

/* 2B. Optional Plot of the Time Series (Descriptive Visualization) */
proc sgplot data=Revenues;
   series x=Year y=Total_Revenues;
   title "Time Series Plot of Total Revenues (1990-2000)";
run;


DATA Revenues_MA;
   SET Revenues;

   Moving_Avg = MEAN(LAG4(Total_Revenues), 
                     LAG3(Total_Revenues), 
                     LAG2(Total_Revenues), 
                     LAG1(Total_Revenues), 
                     Total_Revenues);
RUN;


PROC PRINT DATA=Revenues_MA;
   TITLE '5-Year Moving Average of Total Revenues';
RUN;






proc arima data=Revenues;

   identify var=Total_Revenues nlag=24;
   title 'Stationarity Check on Original Series';
run;


proc arima data=Revenues;
   identify var=Total_Revenues(1);
   title 'Stationarity Check on Differenced Series (1st Difference)';
run;






proc arima data=Revenues;
   identify var=Total_Revenues(1);
   estimate p=1 q=1;
   outlier;
   forecast lead=12 interval=year id=Year out=results;
run;
