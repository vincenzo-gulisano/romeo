package com.vincenzogulisano.util;

import java.io.File;

import com.vincenzogulisano.usecases.linearroad.TupleInput;

import common.util.Util;
import component.operator.Operator;
import component.sink.Sink;
import component.source.Source;
import query.Query;

public class LiebreTest {

    public static void main(String[] args) {
        final String reportFolder = args[0];
        final String inputFile = args[1];
        final String outputFile = reportFolder + File.separator + "temp.csv";

        Query q = new Query();

        Source<String> i1 = q.addTextFileSource("I1", inputFile);

        Operator<String, TupleInput> inputReader = q.addMapOperator(
                "map",
                TupleInput::fromReading);

        Operator<TupleInput, TupleInput> filter = q.addFilterOperator("filter",
                tuple -> tuple.getSpeed() == 0);

        Sink<TupleInput> o1 = q.addTextFileSink("o1", outputFile, true);

        q.connect(i1, inputReader)
                .connect(inputReader, filter)
                .connect(filter, o1);

        q.activate();
        Util.sleep(20000);
        q.deActivate();
    }

}
