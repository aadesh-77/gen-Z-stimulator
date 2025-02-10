import dash
from dash import html, dcc, Input, Output, State
import dash_cytoscape as cyto
import random
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox, colorchooser, filedialog
import json
import csv
import networkx as nx

# Initialize Dash app
app = dash.Dash(__name__)

# Sample Data (Graph Representation)
initial_nodes = [
    {"data": {"id": "1", "label": "User 1", "color": "#00bcd4", "profile": "Profile of User 1"}},
    {"data": {"id": "2", "label": "User 2", "color": "#00bcd4", "profile": "Profile of User 2"}},
    {"data": {"id": "3", "label": "User 3", "color": "#00bcd4", "profile": "Profile of User 3"}},
    {"data": {"id": "4", "label": "User 4", "color": "#00bcd4", "profile": "Profile of User 4"}},
]

initial_edges = [
    {"data": {"source": "1", "target": "2", "weight": 1}},
    {"data": {"source": "2", "target": "3", "weight": 1}},
    {"data": {"source": "3", "target": "4", "weight": 1}},
    {"data": {"source": "4", "target": "1", "weight": 1}},
]

# Dash Layout
app.layout = html.Div([
    html.H1("Gen Z Social Network Simulator", style={"textAlign": "center", "color": "#00bcd4"}),
    html.Div([
        html.Button("Add User", id="add-user", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Add Connection", id="add-connection", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Delete Selected", id="delete-selected", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Export Graph", id="export-graph", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Find Shortest Path", id="find-shortest-path", n_clicks=0, style={"marginRight": "10px"}),
        dcc.Dropdown(
            id="layout-selector",
            options=[
                {"label": "Circle", "value": "circle"},
                {"label": "Grid", "value": "grid"},
                {"label": "Hierarchical", "value": "breadthfirst"},
                {"label": "Radial", "value": "concentric"},
            ],
            value="circle",
            placeholder="Select Layout",
            style={"width": "200px", "display": "inline-block", "marginRight": "10px"},
        ),
        html.Div("Custom Background:", style={"marginTop": "20px"}),
        dcc.Input(
            id="background-color",
            type="text",
            placeholder="Enter a color (e.g., #ffcc00)",
            style={"marginBottom": "20px"},
        ),
    ], style={"textAlign": "center"}),
    cyto.Cytoscape(
        id="network-graph",
        elements=initial_nodes + initial_edges,
        style={"width": "100%", "height": "600px"},
        layout={"name": "circle"},
        stylesheet=[
            {
                "selector": "node",
                "style": {
                    "background-color": "data(color)",
                    "label": "data(label)",
                    "font-size": "14px",
                    "color": "#ffffff",
                    "tooltip": "data(profile)",
                },
            },
            {
                "selector": "edge",
                "style": {
                    "line-color": "#cccccc",
                    "target-arrow-color": "#cccccc",
                    "target-arrow-shape": "triangle",
                },
            },
        ],
        userZoomingEnabled=True,
        userPanningEnabled=True,
    ),
    html.Div(id="shortest-path-output", style={"textAlign": "center", "marginTop": "20px"}),
])

# Dash Callbacks
@app.callback(
    Output("network-graph", "elements"),
    [Input("add-user", "n_clicks"),
     Input("add-connection", "n_clicks"),
     Input("delete-selected", "n_clicks")],
    [State("network-graph", "elements"), State("network-graph", "selectedNodeData"), State("network-graph", "selectedEdgeData")],
)
def update_graph(add_user_clicks, add_connection_clicks, delete_selected_clicks, elements, selected_nodes, selected_edges):
    ctx = dash.callback_context
    if not ctx.triggered:
        return elements

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "add-user":
        new_user_id = str(len([el for el in elements if "source" not in el["data"]]) + 1)
        elements.append({"data": {"id": new_user_id, "label": f"User {new_user_id}", "color": "#00bcd4", "profile": f"Profile of User {new_user_id}"}, "position": {"x": random.randint(50, 500), "y": random.randint(50, 500)}})

    elif button_id == "add-connection":
        if len(elements) > 1:
            source = random.choice([el["data"]["id"] for el in elements if "source" not in el["data"]])
            target = random.choice([el["data"]["id"] for el in elements if "source" not in el["data"]])
            while source == target:
                target = random.choice([el["data"]["id"] for el in elements if "source" not in el["data"]])
            elements.append({"data": {"source": source, "target": target, "weight": 1}})

    elif button_id == "delete-selected":
        if selected_nodes:
            node_ids = [node["id"] for node in selected_nodes]
            elements = [el for el in elements if el["data"].get("id") not in node_ids and el["data"].get("source") not in node_ids and el["data"].get("target") not in node_ids]
        if selected_edges:
            edge_ids = [(edge["source"], edge["target"]) for edge in selected_edges]
            elements = [el for el in elements if (el["data"].get("source"), el["data"].get("target")) not in edge_ids]

    return elements

@app.callback(
    Output("network-graph", "style"),
    Input("background-color", "value"),
    prevent_initial_call=True,
)
def update_background(color):
    return {"width": "100%", "height": "600px", "background-color": color}

@app.callback(
    Output("network-graph", "layout"),
    Input("layout-selector", "value"),
    prevent_initial_call=True,
)
def update_layout(layout_name):
    return {"name": layout_name}

@app.callback(
    Output("network-graph", "generateImage"),
    Input("export-graph", "n_clicks"),
    prevent_initial_call=True,
)
def export_graph_image(n_clicks):
    return {
        "type": "png",
        "action": "download",
    }

@app.callback(
    Output("shortest-path-output", "children"),
    Input("find-shortest-path", "n_clicks"),
    State("network-graph", "elements"),
    State("network-graph", "selectedNodeData"),
)
def find_shortest_path(n_clicks, elements, selected_nodes):
    if n_clicks == 0 or not selected_nodes or len(selected_nodes) != 2:
        return "Please select exactly two nodes to find the shortest path."

    G = nx.Graph()
    for element in elements:
        if "source" in element["data"]:
            G.add_edge(element["data"]["source"], element["data"]["target"], weight=element["data"].get("weight", 1))

    try:
        path = nx.shortest_path(G, source=selected_nodes[0]["id"], target=selected_nodes[1]["id"], weight="weight")
        return f"Shortest path: {' -> '.join(path)}"
    except nx.NetworkXNoPath:
        return "No path exists between the selected nodes."

# Tkinter GUI

def launch_gui():
    root = tk.Tk()
    root.title("Gen Z Social Network Simulator")

    def start_simulator():
        threading.Thread(target=app.run_server, kwargs={"debug": False, "use_reloader": False}, daemon=True).start()
        webbrowser.open("http://127.0.0.1:8050")

    def choose_background():
        color_code = colorchooser.askcolor(title="Choose Background Color")[1]
        if color_code:
            messagebox.showinfo("Background Color", f"Selected Color: {color_code}")

    def export_graph():
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")])
        if file:
            if file.endswith(".json"):
                with open(file, "w") as f:
                    json.dump(initial_nodes + initial_edges, f, indent=4)
            elif file.endswith(".csv"):
                with open(file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Source", "Target", "Label"])
                    for edge in initial_edges:
                        writer.writerow([edge["data"]["source"], edge["data"]["target"], edge["data"].get("label", "")])
            messagebox.showinfo("Export", "Graph exported successfully!")

    tk.Label(root, text="Welcome to the Gen Z Social Network Simulator", font=("Arial", 14), fg="#00bcd4").pack(pady=10)
    tk.Button(root, text="Start Simulator", command=start_simulator, font=("Arial", 12), bg="#00bcd4", fg="white").pack(pady=10)
    tk.Button(root, text="Set Background Color", command=choose_background, font=("Arial", 12), bg="#00bcd4", fg="white").pack(pady=10)
    tk.Button(root, text="Export Graph", command=export_graph, font=("Arial", 12), bg="#00bcd4", fg="white").pack(pady=10)
    tk.Button(root, text="Exit", command=root.quit, font=("Arial", 12), bg="#ff0000", fg="white").pack(pady=10)

    root.mainloop()

# Launch GUI
if __name__ == "__main__":
    launch_gui()
