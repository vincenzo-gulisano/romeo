package com.vincenzogulisano.usecases.linearroad;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import java.util.HashMap;
import java.util.function.Consumer;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import com.vincenzogulisano.javapythoncommunicator.Actionable;
import com.vincenzogulisano.javapythoncommunicator.EnvironmentMonitor;
import com.vincenzogulisano.javapythoncommunicator.StatReporter;
import com.vincenzogulisano.woost.WoostAggregateWithCompression;

import common.metrics.Metrics;
import common.util.Util;
import component.operator.Operator;
import component.sink.Sink;
import component.sink.SinkFunction;
import component.source.Source;
import query.LiebreContext;
import query.Query;

public class QueryCountConsecutiveStops implements Actionable, EnvironmentMonitor {

    private Query q = new Query();
    private long experimentLength;
    private WoostAggregateWithCompression<TupleInput, TupleCarStops> woostAgg;
    private SourceReadFromFile sourceFunction;
    private SinkLogAndLatency sink;
    private String statsFolder;

    public WoostAggregateWithCompression<TupleInput, TupleCarStops> createQuery(String[] args)
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
        options.addOption("n", "nanoSleep", true, "Sleeptime between sends in nanoseconds");
        options.addOption("st", "startingTime", true, "starting time for RL");

        CommandLineParser parser = new DefaultParser();
        CommandLine cmd = parser.parse(options, args);
        statsFolder = cmd.getOptionValue("s");
        String inputFile = cmd.getOptionValue("i");
        long compressionThreshold = Long.parseLong(cmd.getOptionValue("d", String.valueOf(Long.MAX_VALUE)));
        experimentLength = Long.parseLong(cmd.getOptionValue("l"));
        long wa = Long.parseLong(cmd.getOptionValue("wa"));
        long ws = Long.parseLong(cmd.getOptionValue("ws"));
        String outPath = cmd.getOptionValue("o", "");
        boolean writeOut = outPath.equals("") ? false : true;
        InjectorType type = InjectorType.valueOf(cmd.getOptionValue("t", String.valueOf(InjectorType.FIXEDRATE)));
        long nanoSleep = Long.valueOf(cmd.getOptionValue("n", String.valueOf(0)));
        long startingTime = Long.valueOf(cmd.getOptionValue("st", String.valueOf(0)));

        sourceFunction = new SourceReadFromFile(inputFile, type, nanoSleep, startingTime, ws);

        sink = new SinkLogAndLatency("out", new SinkFunction<TupleCarStops>() {

            @Override
            public void accept(TupleCarStops arg0) {
            }

        }, writeOut, outPath);

        Source<TupleInput> s = q.addBaseSource("in", sourceFunction);

        woostAgg = new WoostAggregateWithCompression<>("agg",
                0, 1, ws, wa, new WindowCountStops(), compressionThreshold, statsFolder);

        Operator<TupleInput, TupleCarStops> agg = q.addOperator(woostAgg);

        Sink<TupleCarStops> o1 = q.addSink(sink);

        q.connect(s, agg).connect(agg, o1);

        return woostAgg;

    }

    public void activateQuery() {

        q.activate();
        // ThreadMXBean threadMXBean = ManagementFactory.getThreadMXBean();
        // long[] threadIds = threadMXBean.getAllThreadIds();

        // for (long threadId : threadIds) {
        // ThreadInfo threadInfo = threadMXBean.getThreadInfo(threadId);
        // System.out.println("Thread Name: " + threadInfo.getThreadName() + ", ID: " +
        // threadId);
        // }
        Util.sleep(experimentLength);
        q.deActivate();
    }

    // public void deactivateQuery() {

    //     // q.activate();
    //     // // ThreadMXBean threadMXBean = ManagementFactory.getThreadMXBean();
    //     // // long[] threadIds = threadMXBean.getAllThreadIds();

    //     // // for (long threadId : threadIds) {
    //     // // ThreadInfo threadInfo = threadMXBean.getThreadInfo(threadId);
    //     // // System.out.println("Thread Name: " + threadInfo.getThreadName() + ", ID: "
    //     // + threadId);
    //     // // }
    //     // Util.sleep(experimentLength);
    //     q.deActivate();
    // }

    // public long getQueryDuration() {
    //     return experimentLength;
    // }

    @Override
    public void setStatReporter(StatReporter reporter) {
        System.out.println("SPE - setStatReporter invoked");
        HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();

        System.out.println("SPE - preparing consumers");
        consumers.putAll(sourceFunction.setStatReporter(reporter));
        consumers.putAll(woostAgg.setStatReporter(reporter));
        consumers.putAll(sink.setStatReporter(reporter));
        System.out.println("SPE - Setting metrics type in Liebre");
        LiebreContext.setUserMetrics(Metrics.fileAndConsumer(statsFolder, consumers));

        System.out.println("SPE - Creating statistics");
        sourceFunction.createStatistics();
        woostAgg.createStatistics();
        sink.createStatistics();

    }

    @Override
    public void changeD(long v) {
        System.out.println("SPE - changeD invoked");
        woostAgg.changeD(v);
    }

}
