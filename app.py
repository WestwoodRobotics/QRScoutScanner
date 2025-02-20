from flask import Flask, render_template, request, jsonify, Response
import os
import io
import csv

app = Flask(__name__)

# Define schema defaults in order (35 fields)
schema_defaults = [
    "",    # scouter
    "1",   # matchNumber
    "R1",  # robot
    "0",   # teamNumber
    "",    # Prsp (Starting Position)
    "false",   # noShow
    "",    # CPos (Cage Position)

    "false",   # Mved
    "0",       # timer
    "0",       # CLOA (L1 Coral in auto)
    "0",       # CLTA (L2 Coral in auto)
    "0",       # CLThA (L3 Coral in auto)
    "0",       # CLFA (L4 Coral in auto)
    "0",       # BASA (Barge Algae in auto)
    "0",       # PASA (Processor Algae in auto)
    "false",   # dto (Dislodged Algae in auto)
    "0",       # auf (Auto Foul)

    "false",   # daT (Dislodged Algae in teleop)
    "",        # TGPL (Pickup Location)
    "0",       # CLOT (L1 Coral in teleop)
    "0",       # CLTT (L2 Coral in teleop)
    "0",       # CLThT (L3 Coral in teleop)
    "0",       # CLFT (L4 Coral in teleop)
    "0",       # BAST (Barge Algae in teleop)
    "0",       # PAST (Processor Algae in teleop)
    "false",   # CFPDT (Defense/Cross)
    "false",   # TFOT (Tipped/Fell)
    "0",       # Fou/Tech (Cage Touches)
    "false",   # DEg (Died)

    "No",      # epo (End Position)
    "false",   # DEFEg (Defended)

    "3",       # or (Offense Rating)
    "3",       # dr (Defense Rating)
    "No Card", # yc (Card Status)
    ""         # co (Comments)
]

EXPECTED_FIELDS = len(schema_defaults)  # should be 35

# Translation mappings for specific field indexes
translation_mappings = {
    2: {"R1": "Red 1", "R2": "Red 2", "R3": "Red 3", "B1": "Blue 1", "B2": "Blue 2", "B3": "Blue 3"},
    4: {"R1": "Left", "R2": "Middle", "R3": "Right"},
    6: {"SP1": "Deep", "SP2": "Shallow"},
    18: {"1": "None", "2": "Ground", "3": "Human Player", "4": "Both"},
    29: {"No": "Not Parked", "P": "Parked", "Sc": "Shallow Climb", "Dc": "Deep Climb", "Fc": "Failed Climb"},
    33: {"No Card": "No Card", "Yellow": "Yellow Card", "Red": "Red Card"}
}

def translate_field(index, value):
    ambiguous = False
    if value.endswith(" ●"):
        ambiguous = True
        base = value[:-2]
    else:
        base = value
    if index in translation_mappings and base in translation_mappings[index]:
        translated = translation_mappings[index][base]
    else:
        translated = base
    if ambiguous:
        translated += " ●"
    return translated

def process_record(fields):
    new_record = []
    for i in range(EXPECTED_FIELDS):
        if i < len(fields) and fields[i] != '':
            new_record.append(fields[i])
        else:
            # Append default value with ambiguous marker
            new_record.append(schema_defaults[i] + " ●")

    # Apply translations for fields that have mappings
    for idx in translation_mappings.keys():
        if idx < len(new_record):
            new_record[idx] = translate_field(idx, new_record[idx])
    return new_record

@app.route("/")
def hello_world():
    return render_template("index.html", title="Hello")

@app.route("/upload_qr", methods=["POST"])
def upload_qr():
    qr_data = request.json.get("qr_data")
    if not qr_data:
        return jsonify({"success": False, "message": "No QR data provided"}), 400

    entries_file = "entries.txt"
    if not os.path.exists(entries_file):
        with open(entries_file, "w") as f:
            pass

    with open(entries_file, "r") as f:
        existing_entries = f.read().splitlines()

    if qr_data in existing_entries:
        return jsonify({"success": False, "message": "Duplicate entry"}), 409

    with open(entries_file, "a") as f:
        f.write(qr_data + "\n")

    return jsonify({"success": True, "message": "QR data uploaded successfully"}), 200

@app.route("/records")
def show_records():
    entries_file = "entries.txt"
    records = []
    if os.path.exists(entries_file):
        with open(entries_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    # Split the line by tabs and process the record using the schema
                    fields = [field.strip() for field in line.split('\t')]
                    processed = process_record(fields)
                    records.append(processed)
    return render_template("records.html", title="Records", records=records)

@app.route("/export_csv")
def export_csv():
    entries_file = "entries.txt"
    records = []
    if os.path.exists(entries_file):
        with open(entries_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    fields = [field.strip() for field in line.split('\t')]
                    processed = process_record(fields)
                    # For CSV, replace ambiguous marker with full text for all defaulted fields
                    processed = [field.replace(' ●', ' [Ambiguous Entry]') for field in processed]
                    records.append(processed)
    header = [
        "Scouter Initials", "Match Number", "Robot Position", "Team Number", "Starting Position", "No Show", "Cage Position",
        "Moved", "Timer", "L1 Coral", "L2 Coral", "L3 Coral", "L4 Coral", "Barge Algae", "Processor Algae", "Dislodged Algae", "Fouls",
        "Dislodged Algae", "Pickup Location", "L1 Coral", "L2 Coral", "L3 Coral", "L4 Coral", "Barge Algae", "Processor Algae", "Defense/Cross", "Tipped/Fell", "Cage Touches", "Died",
        "End Position", "Defended", "Offense Rating", "Defense Rating", "Card Status", "Comments"
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    for record in records:
        writer.writerow(record)
    csv_data = output.getvalue()
    return Response(csv_data, mimetype='text/csv', headers={"Content-disposition": "attachment; filename=records.csv"})
