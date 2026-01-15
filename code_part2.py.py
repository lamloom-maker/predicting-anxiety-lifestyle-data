 * copyright (c) 2022 by SAS Institute Inc., Cary NC
 * name    : vf_auto_forecast.sas
 * purpose : Example of using Proc TSMODEL to forecast.
 *           Generate forecast using  auto-forecasting model to include
                more model families: with ESM, IDM, UCM or ARIMAX model
 *-------------------------------------------------------------------
 *  List of strategy specific properties for this Sample
 *  (available as sas MACRO variable to be used in code):
 *     _arimaxInclude            - Specify whether to include ARIMAX model
 *                                 for diagnosis
 *     _esmInclude               - Specify whether to include ESM model
 *                                 for diagnosis
 *     _idmInclude               - Specify whether to include IDM model
 *                                 for diagnosis
 *     _intermittencySensitivity - Sensitivity for intermittency test
 *     _idmMethod                - IDM method
 *     _ucmInclude               - Specify whether to include UCM model
 *                                 for diagnosis
 *     _combInclude              - Specify whether to combine the models
 *                                 other than the external ones for
 *                                 diagnosis
 *     _minobs                   - Minimum number of observations for a
 *                                 non-mean model
 *     _minobsTrend              - Minimum number of observations for a
 *                                 trend model
 *     _minobsSeason             - Minimum number of seasonal cycles for
 *                                 a seasonal model
 *     _holdoutSampleSize        - Size of data to be used for holdout
 *     _holdoutSamplePercent     - Percentage of data to be used for
 *                                 holdout
 *     _selectionCriteria        - Model selection criteria
 *-------------------------------------------------------------------
 * Component needs to produce output datasets and promote to &vf_caslibOut as necessary.
 * Output dataset names:
 *     &vf_outFor   - Required table containing forecast results. It contains
 *                    BY variables, time ID variable, ACTUAL, PREDICT, STD, LOWER, UPPER, ERROR.
 *     &vf_outStat  - Required table containing summary statistics. It contains BY variables,
 *                    _REGION_, _SELECT_, _MODEL_, and various statistics of fit.
 *     &vf_outInformation - Required table containing execution summary. It contains processing information of TSMODEL
 *                          such as number of groups, maximum time ID, number of variables, etc.
 *     &vf_outModelInfo   - Required table containing selected model information. It contains BY variables,
 *                          _MODEL_, _MODELTYPE_, and various flags for seasonal, trend, inputs, events, etc.
 *     &vf_outLog   - Required table containing log messages. It contains
 *                    BY variables, _ERRORNO_, _LOGLEN_, _LOG_.
 *     &vf_outSelect - Required table containing model selection statistics. It contains BY variables,
 *                     _REGION_, _SELECT_, _MODEL_, _SELECTED_ and various statistics of fit.
 *     &vf_outEst   - Optional table containing parameter estimates. It contains _PARM_, _STDERR_,
 *                    _TVALUE_, _PVALUE_, and model information, etc.
 *     &vf_outFmsg  - Optional table containing forecast model selection graph. It contains
 *                    _SPECNAME_, _SPECLEN_, _FMSGPEC_, and _NAME_.
 *     &vf_outComp         - Optional table containing model forecast components. It contains BY variables,
 *                           time ID variable, _ACTUAL_, _PREDICT_, _COMP_, _STD_, _LOWER_, _UPPER_.
 *     &vf_outEvent        - Optional table containing event definitions. It contains the definitions for
 *                           event variables that are specified in an instance of the EVENT object.
 *     &vf_outEventdummy   - Optional table containing event dummy variables. It contains time ID variable,
 *                           _XVAR_(event name), X(values of event).
 *     &vf_outIndep        - Optional table containing independent variables. It contains BY variables, time ID variable,
 *                           _XVAR_(independent name) and X(values of independent variable).
 *-------------------------------------------------------------------*/

/* clean up tables from previous run */
proc cas;
    session &vf_session;
    setsessopt / caslib = "&vf_caslibOut";
    droptable / table = "&vf_outFor"           quiet = 1;
    droptable / table = "&vf_outInformation"   quiet = 1;
    droptable / table = "&vf_outLog"           quiet = 1;
    droptable / table = "&vf_outModelInfo"     quiet = 1;
    droptable / table = "&vf_outSelect"        quiet = 1;
    droptable / table = "&vf_outEst"           quiet = 1;
    droptable / table = "&vf_outComp"          quiet = 1;
    droptable / table = "&vf_outEvent"         quiet = 1;
    droptable / table = "&vf_outEventdummy"    quiet = 1;
    droptable / table = "&vf_outIndep"         quiet = 1;
    droptable / table = "&vf_outFmsg"          quiet = 1;
run;
quit;

*request ODS output outInfo and name it as sforecast_outInformation;
ods output OutInfo = sforecast_outInformation;

/* checking existence of event, independent variables */
%if %UPCASE("&_outtable_outeventInclude") eq "TRUE" %then %do;
    %if "&vf_inEventObj" eq "" and "&vf_events" eq "" %then %do;
        %put WARNING: Cannot create OUTEVENT table because there are no events in the project.;
        %let _outtable_outeventInclude = FALSE;
    %end;
    %if "&vf_inEventObj" ne "" and "&vf_events" eq "" %then %do;
        %put WARNING: OUTEVENT table can be large because it copies event definitions for all events to all BY groups.;
    %end;
%end;
%if %UPCASE("&_outtable_outeventdummyInclude") eq "TRUE" %then %do;
    %if "&vf_events" eq "" %then %do;
        %put WARNING: Cannot create OUTEVENTDUMMY table because there are no events in the project.;
        %let _outtable_outeventdummyInclude = FALSE;
    %end;
%end;
%if %UPCASE("&_outtable_outindepInclude") eq "TRUE" %then %do;
    %if "&vf_indepVars" eq "" %then %do;
        %put WARNING: Cannot create OUTINDEP table because there are no independent variables in the project.;
        %let _outtable_outindepInclude = FALSE;
    %end;
%end;

*run TSMODEL to generate forecasts;
proc tsmodel data = &vf_libIn.."&vf_inData"n
          logcontrol = (error = keep warning = keep)
          %if "&vf_inEventObj" ne "" %then %do;
             inobj = (&vf_inEventObj)
          %end;
          outobj = (
                       outfor  = &vf_libOut.."&vf_outFor"n
                       outstat = &vf_libOut.."&vf_outStat"n
                       outSelect = &vf_libOut.."&vf_outSelect"n
                       outmodelinfo = &vf_libOut.."&vf_outModelInfo"n
                       %if %UPCASE("&_outtable_outestInclude") eq "TRUE" %then outest = &vf_libOut.."&vf_outEst"n;
                       %if %UPCASE("&_outtable_outcompInclude") eq "TRUE" %then outcomp = &vf_libOut.."&vf_outComp"n;
                       %if %UPCASE("&_outtable_outeventInclude") eq "TRUE" %then outevent = &vf_libOut.."&vf_outEvent"n;
                       %if %UPCASE("&_outtable_outeventdummyInclude") eq "TRUE" %then outeventdummy = &vf_libOut.."&vf_outEventDummy"n;
                       %if %UPCASE("&_outtable_outindepInclude") eq "TRUE" %then outindep = &vf_libOut.."&vf_outIndep"n;
                       %if %UPCASE("&_outtable_outfmsgInclude") eq "TRUE" %then outfmsg = &vf_libOut.."&vf_outFmsg"n;
                       )
          outlog  = &vf_libOut.."&vf_outLog"n
          errorstop = YES
          ;

    *define time series ID variable and the time interval;
    id &vf_timeID interval = &vf_timeIDInterval
                  setmissing = &vf_setMissing trimid = LEFT nlformat = yes;

    *define time series and the corresponding accumulation methods;
    %vf_varsTSMODEL;

    *define the by variables if exist;
    %if "&vf_byVars" ne "" %then %do;
       by &vf_byVars;
    %end;

    *using the ATSM (Automatic Time Series Model) package;
    require atsm;

    *starting user script;
    submit;

        /*declare ATSM objects;*/
        /*
        TSDF:     Time series data frame used to group series variables for DIAGNOSE and FORENG objects
        DIAGNOSE: Automatic time series model generation
        FORENG:   Automatic time series model selection and forecasting
        DIAGSPEC: Diagnostic control options for DIAGNOSE object
        OUTFOR:   Collector for FORENG forecasts
        OUTSTAT:  Collector for FORENG forecast performance statistics
        */

        declare object dataFrame(tsdf);
        declare object diagnose(diagnose);
        declare object diagSpec(diagspec);
        declare object inselect(selspec);
        declare object FORECAST(foreng);

        /*initialize the tsdf object and assign the time series roles: setup dependent and independent variables*/
        rc = dataFrame.initialize();
        rc = dataFrame.addY(&vf_depVar);

        *add independent variables to the tsdf object if there is any;
        %if "&vf_indepVars" ne "" %then %do;
            %vf_addXTSMODEL(dataFrame);
        %end;

        /*setup up event information*/
        %if "&vf_inEventObj" ne "" or "&vf_events" ne "" %then %do;
            declare object ev1(event);
            rc = ev1.Initialize();
            %vf_addEvents(dataFrame, ev1);
        %end;

        /*open and setup the diagspec object and enable ESM, IDM, UCM and ARIMAX model class for diagnose;*/
        /*setup time series diagnose specifications*/
        /*open the diagspec object and enable ESM, IDM, UCM, ARIMAX model class for diagnose; */
        rc = diagSpec.open();
        %if %UPCASE("&_esmInclude") eq "TRUE"  %then %do;
            rc = diagSpec.setESM('method', 'BEST');
        %end;
        %if %UPCASE("&_arimaxInclude") eq "TRUE"  %then %do;
            rc = diagSpec.setARIMAX('identify', 'BOTH');
        %end;
        %if %UPCASE("&_idmInclude") eq "TRUE" %then %do;
            rc = diagSpec.setIDM('intermittent',
                                 &_intermittencySensitivity);
            rc = diagSpec.setIDM('METHOD', "&_idmMethod");
        %end;
        %else %do;
            rc = diagSpec.setIDM('intermittent', 1000000);
        %end;
        %if %UPCASE("&_ucmInclude") eq "TRUE" %then %do;
            rc = diagSpec.setUCM();
        %end;


        rc = diagSpec.close();

        /*diagnose time series to generate candidate model list*/
        /*set the diagnose object using the diagspec object and run the diagnose process; */
        rc = diagnose.initialize(dataFrame);
        rc = diagnose.setSpec(diagSpec);

        %vf_setObjectOptions(instance=diagnose, object=diagnose)

        rc = diagnose.Run();
        ndiag = diagnose.nmodels();

        /*Run model selection and forecast*/
        rc = inselect.Open(ndiag);
        rc = inselect.AddFrom(diagnose);
        rc = inselect.close();

        /*initialize the foreng object with the diagnose result and run model selecting and generate forecasts;*/
        rc = forecast.initialize(dataFrame);
        rc = forecast.AddFrom(inselect);

        %vf_setObjectOptions(instance=forecast, object=foreng)

        rc = forecast.setOption('SEASONTEST', 'NONE');
        %if %UPCASE("&_idmInclude") ne "TRUE" %then %do;
            rc = forecast.setOption('INTERMITTENT', 1000000); /* some large number */
        %end;

        rc = forecast.Run();

        /*collect forecast results*/
        declare object outFor(outFor);
        declare object outStat(outStat);
        declare object outSelect(outSelect);
        declare object outModelInfo(outModelInfo);

        %if %UPCASE("&_outtable_outestInclude") eq "TRUE" %then %do;
            declare object outest(outest);
            rc = outest.collect(forecast);
        %end;
        %if %UPCASE("&_outtable_outcompInclude") eq "TRUE" %then %do;
            declare object outcomp(outcomp);
            rc = outcomp.collect(forecast);
        %end;
        %if %UPCASE("&_outtable_outeventInclude") eq "TRUE" %then %do;
            declare object outevent(outevent);
            rc = outevent.collect(ev1);
        %end;
        %if %UPCASE("&_outtable_outeventdummyInclude") eq "TRUE" %then %do;
            declare object outeventdummy(outeventdummy);
            rc = outeventdummy.collect(dataFrame);
        %end;
        %if %UPCASE("&_outtable_outindepInclude") eq "TRUE" %then %do;
            declare object outindep(outindep);
            rc = outindep.collect(forecast);
        %end;
        %if %UPCASE("&_outtable_outfmsgInclude") eq "TRUE" %then %do;
            declare object outfmsg(outfmsg);
            rc = outfmsg.collect(forecast);
        %end;

        /*collect the forecast and statistic-of-fit from the forgen object run results; */
        rc = outFor.collect(forecast);
        rc = outStat.collect(forecast);
        rc = outSelect.collect(forecast);
        rc = outModelInfo.collect(forecast);
    endsubmit;
quit;

*generate outinformation CAS table;
data &vf_libOut.."&vf_outInformation"n;
    set work.sforecast_outInformation;
run;
