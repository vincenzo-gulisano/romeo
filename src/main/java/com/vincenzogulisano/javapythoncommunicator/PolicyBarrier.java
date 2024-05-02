package com.vincenzogulisano.javapythoncommunicator;

public enum PolicyBarrier {
    WEAOB, // Wallclock, Event time, and Aggregate OBlivious
    EAOB, // Event time, and Aggregate OBlivious
    AOB, // Aggregate OBlivious
    WEAAW;// Wallclock, Event time, and Aggregate Aware
}
