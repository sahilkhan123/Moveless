import networkx as nx

import matplotlib.pyplot as plt
from matplotlib import cm
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_pdf import PdfPages

from .. import circuit_to_graph


class ScrollableWindow(QtWidgets.QMainWindow):
    def __init__(self, fig):
        self.qapp = QtWidgets.QApplication([])

        QtWidgets.QMainWindow.__init__(self)
        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.widget.layout().setContentsMargins(0,0,0,0)
        self.widget.layout().setSpacing(0)

        self.fig = fig
        self.canvas = FigureCanvas(self.fig)
        self.canvas.draw()
        self.scroll = QtWidgets.QScrollArea(self.widget)
        self.scroll.setWidget(self.canvas)

        self.nav = NavigationToolbar(self.canvas, self.widget)
        self.widget.layout().addWidget(self.nav)
        self.widget.layout().addWidget(self.scroll)

        self.show()
        exit(self.qapp.exec_())


def plot_graph(G):
    """
        Input: NetworkX graph G
        Return: None
    """
    pos = nx.spring_layout(G)

    nx.draw_networkx_nodes(G, pos, node_color='#77ff77')
    nx.draw_networkx_edges(G, pos)
    labels = nx.get_edge_attributes(G,'weight')
    nx.draw_networkx_edge_labels(G,pos, edge_labels=labels)
    nx.draw_networkx_labels(G,pos)

    plt.axis('off')
    plt.show()

def plot_partitions(G, partitions):
    """
        Input:  NetworkX graph G
                partitions is a list of NetworkX graphs
        Returns: None
    """
    pos = nx.spring_layout(G)

    viridis = cm.get_cmap('viridis', len(partitions)+1)
    cmap = viridis(range(len(partitions)+1))

    node_color_map = []
    for node in G.nodes:
        added = False
        for i, p in enumerate(partitions):
            if node in p:
                added = True
                node_color_map.append(cmap[i])
        if not added:
            node_color_map.append(cmap[-1])

    nx.draw_networkx_nodes(G, pos, node_color=node_color_map)
    nx.draw_networkx_edges(G, pos)
    labels = nx.get_edge_attributes(G,'weight')
    nx.draw_networkx_edge_labels(G,pos, edge_labels=labels)
    nx.draw_networkx_labels(G,pos)

    plt.axis('off')
    plt.show()

def plot_xy(x_range, y_range, scatter=False):
    """
        Input:  (x_range, y_range) - correspond to some function
        Returns: None

        # TODO: plot as a scatter plot
    """
    if scatter:
        plt.plot(x_range, y_range, ".-")
    else:
        plt.plot(x_range, y_range)

    plt.show()

def plot_pair(x1, y1, x2, y2):
    fig, ((ax1), (ax2)) = plt.subplots(2, 1)
    ax1.plot(x1, y1)
    ax2.plot(x2, y2)
    plt.show()

def plot_graphs(x, y, shape):
    fig, axs = plt.subplots(shape[0], shape[1], sharex=True)
    for i in range(shape[0]):
        for j in range(shape[1]):
            axs[i, j].plot(x[i][j], y[i][j])
    plt.show()


def draw_partitions_over_time(G=None, edge_weights_over_time=None, path=None, output_pdf_name=None):
    fig, axes = plt.subplots(ncols=len(path), nrows=1, figsize=(500,5))
    fig.tight_layout()

    for i, p in enumerate(path):
        axes[i]=plt.subplot(1, len(path), i+1, title="T = " + str(i))


        # Update G with edge weights for this slice #
        for ew in edge_weights_over_time[i]:
            lew = list(ew)
            if G.has_edge(lew[0], lew[1]):
                G[lew[0]][lew[1]]["weight"] = edge_weights_over_time[i][ew]

        pos = nx.shell_layout(G)
        partitions = p
        viridis = cm.get_cmap('viridis', len(partitions)+1)
        cmap = viridis(range(len(partitions)+1))

        node_color_map = []
        for node in G.nodes:
            added = False
            for i, p in enumerate(partitions):
                if node in p:
                    added = True
                    node_color_map.append(cmap[i])
            if not added:
                node_color_map.append(cmap[-1])
        nx.draw_networkx_nodes(G, pos, node_color=node_color_map)
        nx.draw_networkx_edges(G, pos)
        labels = nx.get_edge_attributes(G,'weight')
        nx.draw_networkx_edge_labels(G,pos, edge_labels=labels)
        nx.draw_networkx_labels(G,pos)

        plt.axis('off')

    a = ScrollableWindow(fig)
