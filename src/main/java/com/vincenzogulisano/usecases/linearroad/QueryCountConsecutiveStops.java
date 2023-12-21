package com.vincenzogulisano.usecases.linearroad;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import com.vincenzogulisano.javapythoncommunicator.Actionable;
import com.vincenzogulisano.woost.WoostAggregateWithCompression;

import common.metrics.Metrics;
import common.util.Util;
import component.operator.Operator;
import component.sink.Sink;
import component.sink.SinkFunction;
import component.source.Source;
import query.LiebreContext;
import query.Query;

public class QueryCountConsecutiveStops {

    private Query q = new Query();
    private long experimentLength;

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

        CommandLineParser parser = new DefaultParser();
        CommandLine cmd = parser.parse(options, args);
        String reportFolder = cmd.getOptionValue("s");
        String inputFile = cmd.getOptionValue("i");
        long compressionThreshold = Long.parseLong(cmd.getOptionValue("d", String.valueOf(Long.MAX_VALUE)));
        experimentLength = Long.parseLong(cmd.getOptionValue("l"));
        long wa = Long.parseLong(cmd.getOptionValue("wa"));
        long ws = Long.parseLong(cmd.getOptionValue("ws"));
        String outPath = cmd.getOptionValue("o", "");
        boolean writeOut = outPath.equals("") ? false : true;
        InjectorType type = InjectorType.valueOf(cmd.getOptionValue("t", String.valueOf(InjectorType.FIXEDRATE)));
        long nanoSleep = Long.valueOf(cmd.getOptionValue("n", String.valueOf(0)));

        SourceReadFromFile sourceFunction = new SourceReadFromFile(inputFile, type, nanoSleep);

        SinkLogAndLatency sink = new SinkLogAndLatency("out", new SinkFunction<TupleCarStops>() {

            @Override
            public void accept(TupleCarStops arg0) {
            }

        }, writeOut, outPath);

        Source<TupleInput> s = q.addBaseSource("in", sourceFunction);

        WoostAggregateWithCompression<TupleInput, TupleCarStops> woostAgg = new WoostAggregateWithCompression<>("agg",
                0, 1, ws, wa, new WindowCountStops(), compressionThreshold, reportFolder, sourceFunction, sink);

        Operator<TupleInput, TupleCarStops> agg = q.addOperator(woostAgg);

        Sink<TupleCarStops> o1 = q.addSink(sink);

        q.connect(s, agg).connect(agg, o1);

        return woostAgg;

    }

    public void runQuery() {

        q.activate();
        ThreadMXBean threadMXBean = ManagementFactory.getThreadMXBean();
        long[] threadIds = threadMXBean.getAllThreadIds();
        
        for (long threadId : threadIds) {
            ThreadInfo threadInfo = threadMXBean.getThreadInfo(threadId);
            System.out.println("Thread Name: " + threadInfo.getThreadName() + ", ID: " + threadId);
        }
        Util.sleep(experimentLength);
        q.deActivate();
    }

}
