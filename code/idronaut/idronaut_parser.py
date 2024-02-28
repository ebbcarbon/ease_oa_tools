from datetime import datetime
import csv


TIME = "time"
CRUISE_NAME = "cruise_name"
CAST_NAME = "cast_name"
TEMPERATURE_1 = "temperature_1_c"
TEMPERATURE_2 = "temperature_2_c"
DISSOLVED_OXYGEN = "dissolved_oxygen_mg_per_L"
PH = "ph"
PRACTICAL_SALINITY = "practical_salinity"
TURBIDITY = "turbidity_ntu"

CRUISE_NAME = "Cruise name"
CAST_NAME = "cast name"

FIELDNAMES = [TIME, TEMPERATURE_1, PRACTICAL_SALINITY,
              DISSOLVED_OXYGEN, PH,
              TURBIDITY, TEMPERATURE_2,
              CRUISE_NAME, CAST_NAME]

class IdronautParser():
    def __init__(self):
        self.data_dict = {}

        # cache the latest when scanning a file, might have multiple
        self.cruise_name = None
        self.cast_name = None

    def read_file(self, file_):
        """
        read the given file, caching results internally.
        file_: str or opened text file
        """
        if isinstance(file_, str):
            with open(file_, "rt") as idro_file:
                contents = idro_file.read()
                self.add_file_contents(contents)
        else:
            # if it's not a string, we assume it's already been opened
            contents = file_.read()
            self.add_file_contents(contents)

    def add_file_contents(self, contents: str):
        """
        Add the given string to our internal cache

        the given str is probably just read in from a file, but could also be constructed
        manually, or several files combined together etc
        """
        lines = contents.splitlines()
        for line in lines:
            # Take off the whitespace at the ends of the line (including the "newline" characters)
            line = line.strip()

            # skip empty lines
            if line is None or line == "":
                continue

            # Most of the lines are comma-separated, but there are a few that signify the 'cast' or 'cruise'
            # we'll check for these by seeing if the line starts with a 'C' or a 'c' (all other lines should
            # start with numbers indicating time)
            if line[0].lower() == 'c':
                self._read_cruise_cast_header_line(line)
            else:
                # Split the line by comma's
                tokens = line.split(",")

                if len(tokens) == 1:
                    # For now we'll just quietly skip these, there are a lot of them so will get noisy
                    # print(f"Skipping line |{line}|, only one token (maybe weird Idronaut file?)")
                    continue

                # All of the lines in the EASE-OA setup should have 7 tokens. If this line doesn't
                # have 7 tokens, then something's wrong, we need to investigate. The assert will cause
                # the program to stop. We want to print the line that's bad so that we can easily track down
                # where the problem was
                assert len(tokens) == 7, f"File looks wrong, bad number of CSV tokens in line {line}"

                # First token is the date, we'll use this special 'strptime' to convert Idronaut's notion of
                # time into a more standardized Python 'datetime' object -- this will be the 'key' in our
                # dictionary for this row
                date_token = tokens[0]
                if date_token.endswith('**'):
                    date_token = date_token[:-2]
                dt = datetime.strptime(date_token, "%d/%m/%Y %H:%M:%S.%f")

                # Occaisionally we're seeing the Idronaut spit out all 0's. If that's the case,
                # we'll just skip this one (but we print out the time we saw it so that it can be investigated)
                good_line = True
                try:
                    if all(float(value) == 0 for value in tokens[1:]):
                        # Leave off investigation of this for now -- we think it was probably happening
                        # when connected laptop was running out of memory
                        # print(f"Skipping all zeros at {dt}")
                        good_line = False
                except ValueError:
                    good_line = True

                if good_line:
                    # But be careful because we've got some tokens that look like '18.35**'
                    self._add_line_values(dt, tokens)


    def strip_token(self, value):
        """
        Strip off potential '**' appended to value and convert to float
        we're not sure why Idronaut adds this to some values but until we get an answer from
        them we'll just quietly treat this as good data
        """
        if value.endswith('**'):
            value = value[:-2]
        # could put a try here, more debugging info
        float_val = float(value)
        return float_val

    def _add_line_values(self, dt: datetime, tokens: list):
        """
        add the tokens to our internal dictionary at the given time
        """
        # Because of the way the Idronauts are set up for this experiment, we know that temp_1 is at position 1,
        # salinity at 2, etc. If this setup gets changed (via Redas5) then we'll need to change these values
        temp_1 = self.strip_token(tokens[1])
        salinity = self.strip_token(tokens[2])
        do= self.strip_token(tokens[3])
        ph = self.strip_token(tokens[4])
        turbidity = self.strip_token(tokens[5])
        temp_2 = self.strip_token(tokens[6])

        row_dict = {TEMPERATURE_1: temp_1,
                    PRACTICAL_SALINITY: salinity,
                    DISSOLVED_OXYGEN: do,
                    PH: ph,
                    TURBIDITY: turbidity,
                    TEMPERATURE_2: temp_2,
                    CRUISE_NAME: self.cruise_name,
                    CAST_NAME: self.cast_name}
        self.data_dict[dt] = row_dict

    def _read_cruise_cast_header_line(self, line: str):
        """
        this method gets called when we saw a 'c' or 'C' at the start. If this is the cruise name or cast name,
        we store this in our internal attributes so we can include them in the subsequent rows in the csv. This will
        allow us to make one big CSV that has all of the cruises/casts but that we can split apart if we need to
        """
        if line.startswith(CRUISE_NAME):
            self.cruise_name = line[len(CRUISE_NAME):]
        elif line.startswith(CAST_NAME):
            self.cast_name = line[len(CAST_NAME):]

    def output_csv_data(self, output):
        """
        write our internal data to the given path. Note that we don't check if this file is there or not, we always
        just write the file, which may overwrite other work - be careful with this!
        """
        if isinstance(output, str):
            with open(output, "wt") as outfile:
                self._write_csv_data(outfile)
        else:
            self._write_csv_data(output)

    def _write_csv_data(self, outfile):
        """
        write our internal data to the given path. Note that we don't check if this file is there or not, we always
        just write the file, which may overwrite other work - be careful with this!
        """
        writer = csv.DictWriter(outfile, FIELDNAMES)
        writer.writeheader()

        # This is probably unnecessary, the dictionary should be sorted by time anyway. But just to be safe we'll
        # force 'sorting' the keys, which are the times from the files
        times = sorted(self.data_dict.keys())
        for time in times:
            row_dict = {TIME: time}
            row_dict.update(self.data_dict[time])
            writer.writerow(row_dict)
