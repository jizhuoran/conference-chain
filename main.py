import datetime
import networkx as nx
from pyvis.network import Network


class Conference:
    def __init__(
        self,
        name,
        area,
        page,
        column,
        submission_deadline_str,
        notification_date_str,
        submission_deadline=None,
        notification_date=None,
    ):
        self.name = name
        self.area = area
        self.page = page
        self.column = column
        self.submission_deadline_str = submission_deadline_str
        self.notification_date_str = notification_date_str
        if submission_deadline is None and notification_date is None:
            submission_deadline, notification_date = self.compute_day(
                submission_deadline_str, notification_date_str
            )
        self.submission_deadline = submission_deadline
        self.notification_date = notification_date

    def __str__(self):
        return f"{self.name}"

    def compute_day(self, submission_str, notification_str):
        s_year, s_month, s_day = submission_str.split("-")
        n_year, n_month, n_day = notification_str.split("-")
        n_year = int(n_year) - int(s_year)
        s_year = 0

        s_time = int(s_day) + int(s_month) * 30 + int(s_year) * 365
        n_time = int(n_day) + int(n_month) * 30 + int(n_year) * 365

        return s_time, n_time


# load data from CSV file
def load_conferences_from_csv(filename):

    conferences = []
    with open(filename, "r") as file:
        for line in file:
            name, area, submission_deadline, notification_date, page, col = (
                line.strip().split(",")
            )
            conferences.append(
                Conference(
                    name, area, page, col, submission_deadline, notification_date
                )
            )
    return conferences


def apply_filter(conferences, func):
    return [conference for conference in conferences if func(conference)]


def construct_conference_graph(conferences, start_data):

    def norm_day(conferences, start_data):
        _conferences = []
        for conference in conferences:
            if conference.submission_deadline >= start_data:
                _conferences.append(conference)
            else:
                _conferences.append(
                    Conference(
                        conference.name,
                        conference.area,
                        conference.page,
                        conference.column,
                        conference.submission_deadline_str,
                        conference.notification_date_str,
                        conference.submission_deadline + 365,
                        conference.notification_date + 365,
                    )
                )
        return _conferences

    def get_next_conference(conferences, start_data):
        day_to_conference = []
        for conference in conferences:
            day_to_conference.append(
                (conference.submission_deadline - start_data, conference.name)
            )
        return min(day_to_conference, key=lambda x: x[0])[1]

    def same_conference(conference1, conference2):
        return conference1.name[:-1] == conference2.name[:-1]

    def has_in_between(conference1, conference2, conferences):
        return any(
            [
                conference1.notification_date < conference3.submission_deadline
                and conference3.notification_date < conference2.submission_deadline
                for conference3 in conferences
            ]
        )

    _conferences = norm_day(conferences, start_data)
    next_conference = get_next_conference(_conferences, start_data)

    G = nx.DiGraph()

    for conference in _conferences:
        area_to_color = {
            "ARCH": "gold",
            "Security": "blue",
            "PL": "green",
            "Sys": "red",
            "AI": "purple",
        }
        G.add_node(conference, color=area_to_color[conference.area])
        # G.add_node(conference, color= area_to_color[conference.area] if conference.name != next_conference else 'red')

    for conference1 in _conferences:
        for conference2 in _conferences:
            if not same_conference(conference1, conference2):
                if conference1.notification_date < conference2.submission_deadline:
                    if not has_in_between(conference1, conference2, _conferences):
                        G.add_edge(conference1, conference2)
    return G


def draw_conference_graph(G):

    for node in G.nodes():
        G.nodes[node][
            "info"
        ] = f"Area: {node.area}\nSubmission deadline: {node.submission_deadline_str}\nNotification date: {node.notification_date_str}\nPage: {node.page}\nColumn: {node.column}"

    for node in G.nodes():
        G = nx.relabel_nodes(G, {node: str(node.name)})

    # Create a pyvis network with directed flag set to True
    net = Network(notebook=True, directed=True)

    # Identify nodes without in-edges (source nodes)
    source_nodes = [node for node in G.nodes if G.in_degree(node) == 0]

    # Initialize the level map
    level_map = {}

    # Perform topological sort
    topo_order = list(nx.topological_sort(G))

    # Assign levels based on topological order
    for node in topo_order:
        predecessors = list(G.predecessors(node))
        if not predecessors:
            # Source node
            level_map[node] = 0
        else:
            # Level is max level of predecessors plus 1
            level_map[node] = max(level_map[pred] for pred in predecessors) + 1

    # Assign node positions (x, y) based on levels
    positions_per_level = {}
    for node, level in level_map.items():
        positions_per_level.setdefault(level, [])
        positions_per_level[level].append(node)

    # Assign positions to nodes, spreading them horizontally within each level
    node_positions = {}
    for level, nodes_in_level in positions_per_level.items():
        x_spacing = 150  # Adjust horizontal spacing as needed
        y_position = -200 * level  # Adjust vertical spacing as needed
        x_positions = [x_spacing * i for i in range(len(nodes_in_level))]
        for x_pos, node in zip(x_positions, nodes_in_level):
            # net.add_node(node, level=level, x=x_pos, y=y_position, color=G.nodes[node]['color'])

            # Retrieve node attributes
            node_label = G.nodes[node].get("name", str(node))
            node_info = G.nodes[node].get("info", "")

            # Set the 'title' attribute for the hover tooltip
            net.add_node(
                node,
                # label=node_label,
                title=node_info,
                x=x_pos,
                y=y_position,
                level=level,
                color=G.nodes[node]["color"],
            )

    # Add edges from the networkx graph to Pyvis
    # Note: Since we've manually added nodes, ensure edges are correctly added
    for source, target in G.edges():
        net.add_edge(source, target)

    # Customize options to make the graph more sparse and disable physics
    net.set_options(
        """
    var options = {
    "nodes": {
        "font": {
            "size": 32,
            "bold": true
        },
        "size": 30
    },

    "physics": {
        "enabled": false
    },
    "layout": {
        "hierarchical": false
    },
    "edges": {
        "width": 0.1,
        "arrows": {
            "to": {
                "enabled": true,
                "scaleFactor": 1.2
            }
        },
        "selectionWidth": 10
    },
    "interaction": {
        "selectConnectedEdges": true,
        "multiselect": true,
        "hover": true,
        "hoverConnectedEdges": true
    }
    }
    """
    )

    # # Show the network
    net.show("your_submission_opportunity.html")


def start_data(conferences, conf=None, days_from_now=None):
    if conf is None:
        today = datetime.date.today()
        if days_from_now is not None:
            today += datetime.timedelta(days=days_from_now)
        _, s_month, s_day = today.strftime("%Y-%m-%d").split("-")
        return int(s_day) + int(s_month) * 30
    else:
        for conference in conferences:
            if conference.name == conf:
                return conference.submission_deadline


if __name__ == "__main__":
    print("Please enter the days from now you want to submit your paper: ", end="")
    days_from_now = int(input())
    conferences = load_conferences_from_csv("conferences.csv")
    filters = []
    for filter in filters:
        conferences = apply_filter(conferences, filter)
    G = construct_conference_graph(
        conferences, start_data(conferences, days_from_now=days_from_now)
    )
    draw_conference_graph(G)
