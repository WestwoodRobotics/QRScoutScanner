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

@app.route("/team-list")
def team_list():
    entries_file = "entries.txt"
    team_data = {}
    if os.path.exists(entries_file):
        with open(entries_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    fields = [field.strip() for field in line.split('\t')]
                    processed = process_record(fields)
                    team = processed[3]  # Team Number at index 3
                    if team not in team_data:
                        team_data[team] = {"count": 0, "bool_sum": {}, "num_sum": {}}
                    team_data[team]["count"] += 1
                    rec = processed
                    # Boolean fields
                    for idx, key in [(5, "No Show"), (7, "Moved"), (15, "Dislodged Auto"), (17, "Dislodged Teleop"), (25, "Defense/Cross"), (26, "Tipped/Fell"), (28, "Died"), (30, "Defended")]:
                        val = rec[idx].replace(" ●", "").strip().lower()
                        team_data[team]["bool_sum"].setdefault(key, 0)
                        if val == "true":
                            team_data[team]["bool_sum"][key] += 1
                    # Numeric fields
                    for idx, key in [(8, "Timer"), (9, "L1 Coral Auto"), (10, "L2 Coral Auto"), (11, "L3 Coral Auto"), (12, "L4 Coral Auto"), (13, "Barge Algae Auto"), (14, "Processor Algae Auto"), (16, "Auto Fouls"), (19, "L1 Coral Teleop"), (20, "L2 Coral Teleop"), (21, "L3 Coral Teleop"), (22, "L4 Coral Teleop"), (23, "Barge Algae Teleop"), (24, "Processor Algae Teleop"), (27, "Cage Touches"), (31, "Offense Rating"), (32, "Defense Rating")]:
                        try:
                            num = float(rec[idx].replace(" ●", ""))
                        except:
                            num = 0
                        team_data[team]["num_sum"].setdefault(key, 0)
                        team_data[team]["num_sum"][key] += num
    team_stats = []
    for team, data in team_data.items():
        count = data["count"]
        row = {"Team Number": team, "Entry Count": count}
        for key in ["No Show", "Moved", "Dislodged Auto", "Dislodged Teleop", "Defense/Cross", "Tipped/Fell", "Died", "Defended"]:
            perc = (data["bool_sum"].get(key, 0) / count) * 100
            row[key + " (%)"] = f"{perc:.1f}%"
        for key in ["Timer", "L1 Coral Auto", "L2 Coral Auto", "L3 Coral Auto", "L4 Coral Auto", "Barge Algae Auto", "Processor Algae Auto", "Auto Fouls", "L1 Coral Teleop", "L2 Coral Teleop", "L3 Coral Teleop", "L4 Coral Teleop", "Barge Algae Teleop", "Processor Algae Teleop", "Cage Touches", "Offense Rating", "Defense Rating"]:
            avg = data["num_sum"].get(key, 0) / count
            row[key + " (avg)"] = f"{avg:.1f}"
        team_stats.append(row)
    return render_template("team_list.html", title="Team List", teams=team_stats)

@app.route("/team-graph")
def team_graph():
    entries_file = "entries.txt"
    teams = set()
    if os.path.exists(entries_file):
        with open(entries_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    fields = [field.strip() for field in line.split('\t')]
                    processed = process_record(fields)
                    teams.add(processed[3])
    teams = sorted(teams)
    numeric_metrics = {
        "Timer": 8,
        "L1 Coral Auto": 9,
        "L2 Coral Auto": 10,
        "L3 Coral Auto": 11,
        "L4 Coral Auto": 12,
        "Barge Algae Auto": 13,
        "Processor Algae Auto": 14,
        "Auto Fouls": 16,
        "L1 Coral Teleop": 19,
        "L2 Coral Teleop": 20,
        "L3 Coral Teleop": 21,
        "L4 Coral Teleop": 22,
        "Barge Algae Teleop": 23,
        "Processor Algae Teleop": 24,
        "Cage Touches": 27,
        "Offense Rating": 31,
        "Defense Rating": 32
    }
    boolean_metrics = {
        "No Show": 5,
        "Moved": 7,
        "Dislodged Auto": 15,
        "Dislodged Teleop": 17,
        "Defense/Cross": 25,
        "Tipped/Fell": 26,
        "Died": 28,
        "Defended": 30
    }
    return render_template("team_graph.html", title="Team Graph", teams=teams, numeric_metrics=numeric_metrics, boolean_metrics=boolean_metrics)

@app.route("/api/team-data")
def api_team_data():
    team = request.args.get("team")
    metric = request.args.get("metric")
    numeric_keys = ["Timer", "L1 Coral Auto", "L2 Coral Auto", "L3 Coral Auto", "L4 Coral Auto", "Barge Algae Auto", "Processor Algae Auto", "Auto Fouls", "L1 Coral Teleop", "L2 Coral Teleop", "L3 Coral Teleop", "L4 Coral Teleop", "Barge Algae Teleop", "Processor Algae Teleop", "Cage Touches", "Offense Rating", "Defense Rating"]
    boolean_keys = ["No Show", "Moved", "Dislodged Auto", "Dislodged Teleop", "Defense/Cross", "Tipped/Fell", "Died", "Defended"]
    is_numeric = metric in numeric_keys
    entries_file = "entries.txt"
    data_points = []
    mapping = {**{
        "Timer": 8,
        "L1 Coral Auto": 9,
        "L2 Coral Auto": 10,
        "L3 Coral Auto": 11,
        "L4 Coral Auto": 12,
        "Barge Algae Auto": 13,
        "Processor Algae Auto": 14,
        "Auto Fouls": 16,
        "L1 Coral Teleop": 19,
        "L2 Coral Teleop": 20,
        "L3 Coral Teleop": 21,
        "L4 Coral Teleop": 22,
        "Barge Algae Teleop": 23,
        "Processor Algae Teleop": 24,
        "Cage Touches": 27,
        "Offense Rating": 31,
        "Defense Rating": 32
    }, **{
        "No Show": 5,
        "Moved": 7,
        "Dislodged Auto": 15,
        "Dislodged Teleop": 17,
        "Defense/Cross": 25,
        "Tipped/Fell": 26,
        "Died": 28,
        "Defended": 30
    }}
    if os.path.exists(entries_file) and team and metric:
        with open(entries_file, "r") as f:
            records = []
            for line in f:
                line = line.strip()
                if line:
                    fields = [field.strip() for field in line.split('\t')]
                    processed = process_record(fields)
                    if processed[3] == team:
                        records.append(processed)
            records.sort(key=lambda x: int(x[1]))
            
            # Group records by match number
            grouped = {}
            for rec in records:
                match_num = int(rec[1])
                idx = mapping.get(metric)
                if idx is not None:
                    raw = rec[idx].replace(" ●", "").strip().toLowerCase() if hasattr(rec[idx], 'toLowerCase') else rec[idx].replace(" ●", "").strip().lower()
                    if is_numeric:
                        try:
                            value = float(raw)
                        except:
                            value = 0
                    else:
                        value = 1 if raw == "true" else 0
                    grouped.setdefault(match_num, []).append(value)
            
            # Compute averaged value for each match
            for match_num in sorted(grouped.keys()):
                values = grouped[match_num]
                if is_numeric:
                    avg = sum(values) / len(values)
                    data_points.append({"match": match_num, "value": avg})
                else:
                    count_true = sum(values)
                    count_false = len(values) - count_true
                    # Prioritize false in tie
                    final_val = 1 if count_true > count_false else 0
                    data_points.append({"match": match_num, "value": final_val})
    return jsonify(data_points)

@app.route("/custom-graph")
def custom_graph():
    # Define available metrics with their index and type
    available_metrics = {
        "Timer": {"index": 8, "type": "numeric"},
        "L1 Coral Auto": {"index": 9, "type": "numeric"},
        "L2 Coral Auto": {"index": 10, "type": "numeric"},
        "L3 Coral Auto": {"index": 11, "type": "numeric"},
        "L4 Coral Auto": {"index": 12, "type": "numeric"},
        "Barge Algae Auto": {"index": 13, "type": "numeric"},
        "Processor Algae Auto": {"index": 14, "type": "numeric"},
        "Auto Fouls": {"index": 16, "type": "numeric"},
        "L1 Coral Teleop": {"index": 19, "type": "numeric"},
        "L2 Coral Teleop": {"index": 20, "type": "numeric"},
        "L3 Coral Teleop": {"index": 21, "type": "numeric"},
        "L4 Coral Teleop": {"index": 22, "type": "numeric"},
        "Barge Algae Teleop": {"index": 23, "type": "numeric"},
        "Processor Algae Teleop": {"index": 24, "type": "numeric"},
        "Cage Touches": {"index": 27, "type": "numeric"},
        "Offense Rating": {"index": 31, "type": "numeric"},
        "Defense Rating": {"index": 32, "type": "numeric"},
        "No Show": {"index": 5, "type": "boolean"},
        "Moved": {"index": 7, "type": "boolean"},
        "Dislodged Auto": {"index": 15, "type": "boolean"},
        "Dislodged Teleop": {"index": 17, "type": "boolean"},
        "Defense/Cross": {"index": 25, "type": "boolean"},
        "Tipped/Fell": {"index": 26, "type": "boolean"},
        "Died": {"index": 28, "type": "boolean"},
        "Defended": {"index": 30, "type": "boolean"}
    }
    
    x_metric = request.args.get("x_metric")
    y_metric = request.args.get("y_metric")
    data_points = []

    if x_metric and y_metric and x_metric in available_metrics and y_metric in available_metrics:
        entries_file = "entries.txt"
        team_data = {}
        if os.path.exists(entries_file):
            with open(entries_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        fields = [field.strip() for field in line.split('\t')]
                        processed = process_record(fields)
                        team = processed[3]
                        team_data.setdefault(team, []).append(processed)
        
        # Compute averages per team for selected metrics, excluding ambiguous entries
        for team, records in team_data.items():
            x_sum = 0.0
            x_count = 0
            y_sum = 0.0
            y_count = 0
            x_idx = available_metrics[x_metric]["index"]
            y_idx = available_metrics[y_metric]["index"]
            x_type = available_metrics[x_metric]["type"]
            y_type = available_metrics[y_metric]["type"]

            for rec in records:
                # Process x metric
                val_x_raw = rec[x_idx] if len(rec) > x_idx else ""
                if "●" in val_x_raw:
                    # Skip ambiguous entry
                    pass
                else:
                    if x_type == "numeric":
                        try:
                            num = float(val_x_raw)
                            x_sum += num
                            x_count += 1
                        except:
                            pass
                    else:
                        val_x = val_x_raw.strip().lower()
                        v = 1 if val_x == "true" else 0
                        x_sum += v
                        x_count += 1

                # Process y metric
                val_y_raw = rec[y_idx] if len(rec) > y_idx else ""
                if "●" in val_y_raw:
                    pass
                else:
                    if y_type == "numeric":
                        try:
                            num = float(val_y_raw)
                            y_sum += num
                            y_count += 1
                        except:
                            pass
                    else:
                        val_y = val_y_raw.strip().lower()
                        v = 1 if val_y == "true" else 0
                        y_sum += v
                        y_count += 1

            if x_count > 0 and y_count > 0:
                avg_x = x_sum / x_count
                avg_y = y_sum / y_count
                data_points.append({"team": team, "x": avg_x, "y": avg_y})

    return render_template("custom_graph.html", available_metrics=available_metrics, data_points=data_points, selected_x=x_metric, selected_y=y_metric)

@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')
