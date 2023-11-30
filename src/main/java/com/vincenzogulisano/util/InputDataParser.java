package com.vincenzogulisano.util;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

import com.vincenzogulisano.usecases.linearroad.TupleInput;


public class InputDataParser {
    public static void main(String[] args) {

        String inputFile = args[0];
        String outputFile = args[1];
        int xway = Integer.parseInt(args[2]);
        long timestampShift = Long.parseLong(args[3]);

        try (BufferedReader reader = new BufferedReader(new FileReader(inputFile));
                FileWriter writer = new FileWriter(outputFile)) {

            String line;
            while ((line = reader.readLine()) != null) {
                TupleInput t = TupleInput.fromReading(line);
                if (t.getType() == 0) {
                    // Need to write out explicitely since timestamp field is final
                    writer.write(t.getType() + "," + t.getTimestamp() + timestampShift + "," + t.getVid() + ","
                            + t.getSpeed() + "," + xway + "," + t.getLane() + "," + t.getDir() + "," + t.getSeg() + ","
                            + t.getPos() + "\n");
                }
            }

        } catch (IOException e) {
            System.out.println("An error occurred while handling the file: " + e.getMessage());
        }
    }
}
