import datetime
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

class Conference:
    def __init__(self, name, area, submission_deadline, notification_date, page, column):
        self.name = name
        self.area = area
        self.submission_deadline = submission_deadline
        self.notification_date = notification_date
        self.page = page
        self.column = column

    def __str__(self):
        return f'{self.name}'


#load data from CSV file
def load_conferences_from_csv(filename):
    def compute_day(submission_str, notification_str):
        s_year, s_month, s_day = submission_str.split('-')
        n_year, n_month, n_day = notification_str.split('-')
        n_year = int(n_year) - int(s_year)
        s_year = 0

        s_time = int(s_day) + int(s_month) * 30 + int(s_year) * 365
        n_time = int(n_day) + int(n_month) * 30 + int(n_year) * 365

        return s_time, n_time

    conferences = []
    with open(filename, 'r') as file:
        for line in file:
            name, area, submission_deadline, notification_date, page, col = line.strip().split(',')
            submission_deadline, notification_date = compute_day(submission_deadline, notification_date)
            conferences.append(Conference(name, area, submission_deadline, notification_date, page, col))
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
                _conferences.append(Conference(conference.name, conference.area, conference.submission_deadline + 365, conference.notification_date + 365, conference.page, conference.column))
        return _conferences
    
    def get_next_conference(conferences, start_data):
        day_to_conference = []
        for conference in conferences:
            day_to_conference.append((conference.submission_deadline - start_data, conference.name))
        return min(day_to_conference, key=lambda x: x[0])[1]

    def same_conference(conference1, conference2):
        return conference1.name[:-1] == conference2.name[:-1]

    def has_in_between(conference1, conference2, conferences):
        return any([conference1.notification_date < conference3.submission_deadline and conference3.notification_date < conference2.submission_deadline for conference3 in conferences])

    _conferences = norm_day(conferences, start_data)
    next_conference = get_next_conference(_conferences, start_data)

    G = nx.DiGraph()

    for conference in _conferences:
        area_to_color = {'ARCH': 'gold', 'Security': 'blue', 'PL': 'green', 'Sys': 'yellow', 'AI': 'purple'}
        G.add_node(conference, color= area_to_color[conference.area] if conference.name != next_conference else 'red')

    for conference1 in _conferences:
        for conference2 in _conferences:
            if not same_conference(conference1, conference2):
                if conference1.notification_date < conference2.submission_deadline:
                    if not has_in_between(conference1, conference2, _conferences):
                        G.add_edge(conference1, conference2)
    return G

def draw_conference_graph(G):

    for node in G.nodes():
        G = nx.relabel_nodes(G, {node: str(node)})

    # Create a pyvis network
    net = Network(notebook=True, directed=True)
    net.from_nx(G)

    # Customize options
    # net.set_options("""
    # var options = {
    # "nodes": {
    #     "color": {
    #     "border": "rgba(0,0,0,0.3)",
    #     "background": "rgba(97,189,79,1)"
    #     },
    #     "font": {
    #     "color": "#ffffff"
    #     }
    # },
    # "edges": {
    #     "color": {
    #     "color": "rgba(0,0,0,0.3)"
    #     }
    # }
    # }
    # """)

    # Visualize
    net.show("conference_chain.html")

def start_data(conferences, conf=None, days_from_now=None):
    if conf is None:
        today = datetime.date.today()
        if days_from_now is not None:
            today += datetime.timedelta(days=days_from_now)
        _, s_month, s_day = today.strftime('%Y-%m-%d').split('-')
        return int(s_day) + int(s_month) * 30
    else:
        for conference in conferences:
            if conference.name == conf:
                return conference.submission_deadline

conferences = load_conferences_from_csv('conferences.csv')
filters = [lambda x: x.area == 'ARCH']
for filter in filters:
    conferences = apply_filter(conferences, filter)

G = construct_conference_graph(conferences, start_data(conferences, days_from_now=50))
draw_conference_graph(G)
