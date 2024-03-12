package com.vincenzogulisano.usecases.synthetic;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Consumer;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.Actionable;
import com.vincenzogulisano.javapythoncommunicator.EnvironmentMonitor;
import com.vincenzogulisano.javapythoncommunicator.StatReporter;
import com.vincenzogulisano.usecases.linearroad.SinkLogAndLatency;
import com.vincenzogulisano.usecases.linearroad.TupleCarStops;
import com.vincenzogulisano.usecases.linearroad.InjectorType;
import com.vincenzogulisano.util.EpisodesLogger;
import com.vincenzogulisano.util.ThreadCPUMonitor;
import com.vincenzogulisano.woost.WoostAggregateWithCompression;

import common.metrics.Metrics;
import common.util.Util;
import component.operator.Operator;
import component.sink.Sink;
import component.sink.SinkFunction;
import component.source.Source;
import query.LiebreContext;
import query.Query;

public class QuerySynthetic implements Actionable, EnvironmentMonitor {

    private Query q = new Query();
    private long experimentLength;
    private WoostAggregateWithCompression<TupleInput, TupleInput> woostAgg;
    private SourceReadFromFile sourceFunction;
    private SinkLogAndLatency<TupleInput> sink;
    private ThreadCPUMonitor threadCPUMonitor;
    private long compressionThreshold;
    private String statsFolder;
    private StatReporter reporter;
    private EpisodesLogger episodesLogger;
    private boolean firstEpisodeStarted;
    private long startingTimeMinimum;
    private long startingTimeMaximum;
    private long wa;
    private long ws;
    private Random r;
    private boolean randomizeSeed;

    public final static long sleepBeforeRealRate = 1000;

    // The name of this Logger will be "org.apache.logging.Child"
    public Logger logger = LogManager.getLogger();

    public static void main(String[] args) throws ParseException, IOException {
        QuerySynthetic q = new QuerySynthetic();
        q.createQuery(args);
        q.setStatReporter(new StatReporter() {

            @Override
            public void report(long ts, String id, double value) {

            }

            @Override
            public void setResetRequest() {

            }

            @Override
            public boolean getResetAcknowledged() {
                return true;
            }

            @Override
            public void setResetCompleted() {

            }

            @Override
            public void addSendStateToken(long clockTimeBarrier, long eventTimeBarrier) {

            }

            @Override
            public void registerLogger(EpisodesLogger logger) {

            }

            @Override
            public void close() {

            }

        });
        q.activateQuery();
        Util.sleep(q.experimentLength);
        q.close();

    }

    public void createQuery(String[] args)
            throws ParseException, IOException {

        Options options = new Options();
        options.addOption("i", "inputFile", true, "Input file path");
        options.addOption("s", "statsFolder", true, "Output folder for stats");
        options.addOption("d", "compressionThreshold", true, "Defines the compression threshold");
        options.addOption("l", "experimentLength", true, "Length of the experiment in milliseconds");
        options.addOption("wa", "windowAdvance", true, "Aggregate's window advance");
        options.addOption("ws", "windowSize", true, "Aggregate's window size");
        options.addOption("o", "outputFile", true, "File to output tuples");
        options.addOption("t", "injectorType", true, "Type of injector");
        // options.addOption("n", "nanoSleep", true, "Sleeptime between sends in
        // nanoseconds");
        // options.addOption("stmin", "startingTimeMinimum", true, "minimum starting
        // time for RL");
        // options.addOption("stmax", "startingTimeMaximum", true, "maximum starting
        // time for RL");
        // options.addOption("log4j", "log4jConfigFile", true, "log4j config file");
        // options.addOption("rer", "randomizeEpisodeRate", true,
        // "If true, each episode resets the random seed to the current time");

        CommandLineParser parser = new DefaultParser();
        CommandLine cmd = parser.parse(options, args);

        statsFolder = cmd.getOptionValue("s");
        String inputFile = cmd.getOptionValue("i");
        compressionThreshold = Long.parseLong(cmd.getOptionValue("d", String.valueOf(Long.MAX_VALUE)));
        experimentLength = Long.parseLong(cmd.getOptionValue("l"));
        wa = Long.parseLong(cmd.getOptionValue("wa"));
        ws = Long.parseLong(cmd.getOptionValue("ws"));
        String outPath = cmd.getOptionValue("o", "");
        boolean writeOut = outPath.equals("") ? false : true;
        InjectorType type = InjectorType.valueOf(cmd.getOptionValue("t", String.valueOf(InjectorType.FIXEDRATE)));
        // long nanoSleep = Long.valueOf(cmd.getOptionValue("n", String.valueOf(0)));
        // startingTimeMinimum = Long.valueOf(cmd.getOptionValue("stmin",
        // String.valueOf(0)));
        // startingTimeMaximum = Long.valueOf(cmd.getOptionValue("stmax",
        // String.valueOf(0)));
        // randomizeSeed = Boolean.valueOf(cmd.getOptionValue("rer", "False"));

        r = new Random(0);

        episodesLogger = new EpisodesLogger(statsFolder + File.separator + "episodes.csv");
        firstEpisodeStarted = false;

        sourceFunction = new SourceReadFromFile(inputFile, type, startingTimeMinimum, ws);

        sink = new SinkLogAndLatency<>("out", new SinkFunction<TupleInput>() {

            @Override
            public void accept(TupleInput arg0) {
            }

        }, writeOut, outPath);

        Source<TupleInput> s = q.addBaseSource("in", sourceFunction);

        woostAgg = new WoostAggregateWithCompression<>("agg",
                0, 1, ws, wa, new WindowSynthetic(), compressionThreshold, statsFolder);

        Operator<TupleInput, TupleInput> agg = q.addOperator(woostAgg);

        Sink<TupleInput> o1 = q.addSink(sink);

        q.connect(s, agg).connect(agg, o1);

        threadCPUMonitor = new ThreadCPUMonitor(List.of("in", "agg", "out"));

    }

    public void activateQuery() {

        q.activate();
        threadCPUMonitor.startMonitoring();

        // Forcing a "reset" here to make sure we wait for the injector from the very
        // first episode
        reset();

        // Util.sleep(experimentLength);

    }

    @Override
    public void setStatReporter(StatReporter reporter) {

        this.reporter = reporter;
        this.reporter.registerLogger(episodesLogger);

        logger.debug("SPE - setStatReporter invoked");
        HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();

        logger.debug("SPE - preparing consumers");
        consumers.putAll(sourceFunction.setStatReporter(reporter));
        consumers.putAll(woostAgg.setStatReporter(reporter));
        consumers.putAll(sink.setStatReporter(reporter));
        consumers.putAll(threadCPUMonitor.setStatReporter(reporter));

        logger.debug("SPE - Setting metrics type in Liebre");
        LiebreContext.setUserMetrics(Metrics.fileAndConsumer(statsFolder, consumers));

        logger.debug("SPE - Creating statistics");
        sourceFunction.createStatistics();
        woostAgg.createStatistics();
        sink.createStatistics();
        threadCPUMonitor.createStatistics();

    }

    public long getWS_WA_Ceil() {
        return (long) Math.ceil((double) ws / (double) wa);
    }

    public long getContributingWindows(long ts) {
        return ts % wa >= ws % wa && ws % wa != 0L ? (getWS_WA_Ceil() - 1) : getWS_WA_Ceil();
    }

    public long getEarliestWinStartTS(long ts) {
        return (long) Math.max((double) ((ts / wa - this.getContributingWindows(ts) + 1L) * wa), 0.0);
    }

    @Override
    public void changeD(long v) {
        logger.debug("SPE - changeD invoked");
        episodesLogger.writeActionEvent(Long.toString(v));
        long newCompression = (long) ((double) ws * ((double) v / 10.0));
        long latestEventTime = woostAgg.changeD(newCompression);
        long nextEventTimeOutput = getEarliestWinStartTS(latestEventTime) + ws;
        logger.debug("Next batch of outputs to be produced by A at {}", nextEventTimeOutput);
        if (nextEventTimeOutput == latestEventTime + 1) {
            logger.debug("Since is the event time after this, taking the next batch of outputs");
            nextEventTimeOutput += wa;
        }
        long latestClockTime = System.currentTimeMillis() / 1000;
        logger.debug(
                "D changed to {} at event time {} and clock time {}. Barriers: event time >= {} and clock time >= {}",
                v, latestEventTime, latestClockTime, nextEventTimeOutput + 1, latestClockTime + 1);

        logger.debug("Since D has changed, adding a token to the state monitor");
        reporter.addSendStateToken(latestClockTime + 1, nextEventTimeOutput + 1);

    }

    @Override
    public void reset() {

        logger.debug("SPE - Got a RESET request");

        if (randomizeSeed) {
            r = new Random(System.currentTimeMillis());
        }

        long startingTS = startingTimeMinimum + r.nextInt((int) (startingTimeMaximum - startingTimeMinimum) + 1);
        logger.debug("SPE - Updating source starting time to " + startingTS);
        sourceFunction.setStartingTS(startingTS);

        logger.debug("SPE - Synchronizing with Source to initiate the procedure");
        sourceFunction.registerResetRequest();

        if (!firstEpisodeStarted) {
            logger.debug(
                    "This is the first episode, and the source has not been authorized to start sending tuples. Authorizing it before continuing with the reset");
            sourceFunction.notifyFirstEpisodeCanStart();
        }

        if (firstEpisodeStarted) {
            episodesLogger.writeEndEvent();
        }

        while (!sourceFunction.getResetAck()) {
            Util.sleep(50);
        }
        logger.debug("SPE - The source is no longer injecting tuples, resetting Agg, Sink, and Source");
        woostAgg.reset();
        while (!woostAgg.getResetAck()) {
            Util.sleep(50);
        }
        logger.debug("Got Ack from the Agg");
        sink.reset();
        // while (!sink.getResetAck()) {
        // Util.sleep(500);
        // }
        logger.debug("Sink reset");

        // logger.debug("Sleeping 2 seconds before resetting the compression
        // threshold");
        // Util.sleep(2000);

        logger.debug("Reset compression threshold of the Aggregate to " + compressionThreshold);
        woostAgg.changeD(compressionThreshold);

        // logger.debug("Sleeping 2 seconds before giving green light for state filling
        // tuples");
        // Util.sleep(2000);

        sourceFunction.giveGreenlightToStartSendingStateFillingTuples();

        while (!sourceFunction.areAllStateFillingTuplesSent()) {
            Util.sleep(50);
        }
        logger.debug("SPE - the source has sent all the state filling tuples too");

        sourceFunction.giveGreenlightToStartSendingRealRateTuples();

        firstEpisodeStarted = true;
        // Util.sleep(sleepBeforeRealRate);
        episodesLogger.writeStartEvent();

        logger.debug("Resetting the EnvironmentStateCalculator");
        reporter.setResetRequest();
        while (!reporter.getResetAcknowledged()) {
            Util.sleep(50);
        }
        reporter.setResetCompleted();
        logger.debug("EnvironmentStateCalculator is now reset");

        logger.debug("Since the reset is complete, adding a token to the state monitor");
        long latestEventTime = woostAgg.getLatestEventTime();
        long latestClockTime = System.currentTimeMillis() / 1000;
        reporter.addSendStateToken(latestClockTime, latestEventTime);

    }

    @Override
    public void close() {
        logger.debug("Received close command");

        // Log the end of the final episode
        episodesLogger.writeEndEvent();
        episodesLogger.writeCloseEvent();
        episodesLogger.close();

        threadCPUMonitor.stopMonitoring();
        // q.deActivate();
    }

}
