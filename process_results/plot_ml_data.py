#!/usr/bin/env python3
# coding: utf-8

__author__ = 'Mário Antunes'
__version__ = '0.1'
__email__ = 'mariolpantunes@gmail.com'
__status__ = 'Development'


import argparse
import enum
import logging
import statistics

import pandas as pd
import plotly.graph_objects as go
import tqdm
from tqdm.contrib import tzip

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class Aggregation(enum.Enum):
    min = 'min'
    max = 'max'
    mean = 'mean'
    median = 'median'

    def __str__(self):
        return self.value


def multi_plot(df, args, addAll = True):
    fig = go.Figure()

    # Get the models within the CSV file
    models = df['model'].unique().tolist()
    models.sort()

    # Generate all the data for plotly
    for m in tqdm.tqdm(models):
        model_data = df.loc[df['model']==m]
        data_x = model_data['malicious'].tolist()
        data_y = model_data['dataset_len'].tolist()

        data_z = []
        for i, j in tzip(data_x, data_y, leave=False):
            temp_data = model_data.loc[(model_data['malicious']==i) & (model_data['dataset_len']==j),['mcc']]
            
            if args.a is Aggregation.max:
                result = max(temp_data['mcc'].tolist())
            elif args.a is Aggregation.min:
                result = min(temp_data['mcc'].tolist())
            elif args.a is Aggregation.mean:
                result = statistics.mean(temp_data['mcc'].tolist())
            else:
                result = statistics.median(temp_data['mcc'].tolist())

            data_z.append(result)

        fig.add_trace(
            go.Scatter3d(
                x=data_x,
                y=data_y,
                z=data_z,
                mode='markers',
                marker_color = models.index(m),
                name = m
            )
        )

    axis = dict(range = [-0.1, 1])
    fig.update_layout(scene=dict(zaxis = axis))
    fig.update_layout(scene = dict(
                    xaxis_title='Nº Malicious users',
                    yaxis_title='Nº of training examples',
                    zaxis_title='MCC'))
    button_all = dict(label = 'All', method = 'restyle', args = [{'visible': [True]*len(models), 'title': 'All', 'showlegend':True}])

    def create_layout_button(column):
        visible = []
        for m in models:
            if m == column:
                visible.append(True)
            else:
                visible.append(False)
        return dict(label = column, method = 'restyle', args = [{'visible': visible, 'title': column, 'showlegend': True}])
    buttons = ([button_all] * addAll) + list(map(lambda column: create_layout_button(column), models))
    fig.update_layout(updatemenus=[go.layout.Updatemenu(active = 0, buttons = buttons)])
    
    fig.show()


def main(args):
    # load CSV
    data = pd.read_csv(args.i, header = 0)
    multi_plot(data,args)

    #fig = px.scatter_3d(data, x='malicious', y='dataset_len', z='mcc', color='model')
    #fig.show()

    #fig = plt.figure()
    #ax = fig.add_subplot(111, projection='3d')
    #ax.scatter(x,y,z)
    #ax.plot_trisurf(x,y,z)
    #plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot data from the ML dataset')
    parser.add_argument('-i', type=str, help='output dataset CSV', default='output.csv')
    #parser.add_argument('-l', type=int, help='number of iterations (loops)', default=20)
    #parser.add_argument('-t', type=int, help='MNIST test dataset', default='dataset/mnist_test.csv')
    #parser.add_argument('-o', type=str, help='output folder', default='results')
    parser.add_argument('-a', type=Aggregation, choices=list(Aggregation), default='max')
    args = parser.parse_args()
    
    main(args)