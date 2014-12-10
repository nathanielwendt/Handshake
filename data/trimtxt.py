
with open('animals-trim.txt', 'w') as output:
    with open('animals.txt', 'r+') as file:
        delim = ""
        for line in file:
            line = line.strip()
            if not line or\
                    len(line.split(" ")) > 1 or\
                    line.find("-") > 0 or\
                    len(line) > 8:
                continue

            output.write(delim + line)
            delim = "\n"
