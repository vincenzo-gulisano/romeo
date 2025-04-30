# bash command that, given a text file, finds all the rows that start with a timestamp in the format HH:MM:SS.XXX and are followed by "DEBUG SourceReadFromFile - Got a reset request, Resetting the source!" or "DEBUG SourceReadFromFile - Sleeping 1000 ms before starting for real". For each row, print start,timestamp if you find the first match or end,timestamp for the second match. Convert timestamps in unix format

rm $2.tmp

grep -E "^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} DEBUG .+ - SPE - (Got a RESET request|the source has sent all the state filling tuples too|Updating source starting time to )" $1 | while read -r line; do
    timestamp=$(echo "$line" | grep -oE "^[0-9]{2}:[0-9]{2}:[0-9]{2}")
    unix_timestamp=$(date -d "$timestamp" +"%s")
    if [[ "$line" == *"Got a RESET request"* ]]; then
        echo "$unix_timestamp" >> $2.tmp
    elif [[ "$line" == *"the source has sent all the state filling tuples too"* ]]; then
        echo "$unix_timestamp" >> $2.tmp
    elif [[ "$line" == *"Updating source starting time to "* ]]; then
        start_event_time=$(echo "$line" | sed 's/.* to \([0-9]*\)$/\1/')
        echo "$start_event_time" >> $2.tmp
    fi
done

echo "start, eventtime, end" > $2
awk '{printf "%s%s", $0, (NR%3==0 ? "\n" : ",")}' "$2.tmp" >> $2
rm $2.tmp