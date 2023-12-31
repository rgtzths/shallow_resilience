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
import numpy as np
import tqdm
from tqdm.contrib import tzip
from scipy.interpolate import griddata

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

    colors = {
        "LR" : "#636efa",
        "SVM" : "#ef553b",
        "KNN(1)" : "#00cc96",
        "KNN(3)" : "#ab63fa",
        "KNN(5)" : "#ffa15a",
        "KNN(7)" : "#19d3f3",
        "KNN(9)" : "#ff6692",
        "DT" : "#b6e880",
        "ANN" : "#ff97ff",
        "RF" : "#fecb52",
        "VF(hard)" : "#66b100",
        "VF(soft)" : "#efb03b"
    }

    # Get the models within the CSV file
    if not args.m: 
        models = df['model'].unique().tolist()
    else:
        models = args.m

    # Generate all the data for plotly
    for m in tqdm.tqdm(models):
        model_data = df.loc[df['model']==m]
        data_x = [round(x/20,2) for x in model_data['malicious'].tolist()]
        data_y = [round(x/60000,2) for x in model_data['dataset_len'].tolist()]

        data_z = []
        for i, j in tzip(model_data['malicious'].tolist(), model_data['dataset_len'].tolist(), leave=False):
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
                marker_color = colors[m], 
                name = m
            )
        )

    mycolorscale = [[0, '#aa9ce2'],
                    [1, '#aa9ce2']]
    
    if len(models) > 1:
        height=0.7
        x= np.linspace(-0.1, 1.1, 75)
        y= np.linspace(0.2, 1.1, 100)
        z= height*np.ones((100, 75))

        fig.add_trace(go.Surface(x=x, y=y, z=z, colorscale=mycolorscale, showscale=False, opacity=0.8))

    
    elif args.x != None and args.y != None:
        x= np.linspace(args.x, 1.1, 75)
        y= args.y*np.ones(100)
        z= np.reshape(np.linspace(-0.1, 0.7, 7500), (75, 100))

        fig.add_trace(go.Surface(x=x, y=y, z=z, colorscale=mycolorscale, showscale=False))

        x= args.x*np.ones(75)
        y= np.linspace(args.y, 1.1, 100)
        np.random.shuffle(y)
        z= [np.linspace(-0.1, 0.7, 75) for x in range(100)]
        
        fig.add_trace(go.Surface(x=x, y=y, z=z, colorscale=mycolorscale, showscale=False))

    camera = dict(
        center=dict(x=0, y=0, z=0),
        eye=dict(x=1, y=2, z=0.4)
    )

    fig.update_layout(scene=dict(xaxis = dict(range = [-0.1, 1.1], dtick=0.2), yaxis=dict(range = [0.2, 1.1], dtick=0.2), zaxis = dict(range = [-0.1, 1], dtick=0.2)), scene_camera=camera)
    fig.update_layout(scene = dict(
                    xaxis_title='% of malicious users',
                    yaxis_title='% of training examples',
                    zaxis_title='MCC'))
    fig.update_layout(scene_aspectmode='cube')
    
    fig.update_layout(
        height=550,
        width=600,
        margin=dict(t=0, b=0, l=0, r=0),
    )
    
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
    
    if args.f == "pdf":
        fig.write_image(args.o)

    elif args.f == "html":
        fig.update_layout(updatemenus=[go.layout.Updatemenu(active = 0, buttons = buttons, x=0.1, xanchor="left", y=1.1, yanchor="top")])
        fig.write_html(args.o, include_plotlyjs=False, include_mathjax=False, full_html=False)

    else:
        fig.update_layout(updatemenus=[go.layout.Updatemenu(active = 0, buttons = buttons, x=0.1, xanchor="left", y=1.1, yanchor="top")])
        fig.show(renderer=args.f)


def main(args):
    # load CSV
    data = pd.read_csv(args.i, header = 0)
    multi_plot(data,args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot data from the ML dataset')
    parser.add_argument('-i', type=str, help='output dataset CSV', default='output.csv')
    parser.add_argument('-a', type=Aggregation, choices=list(Aggregation), default='min')
    parser.add_argument('-f', type=str, help="Choose the format of the image (html, pdf, or browser)", default='browser')
    parser.add_argument('-o', type=str, help="Output file name", default='plots/figure1.pdf')
    parser.add_argument('-m', type=str, nargs="+", help="Models to consider", default=None)
    parser.add_argument('-x', type=float, help="Nº malicious users breaking point", default=None)
    parser.add_argument('-y', type=float, help="Percentage of the dataset breaking point", default=None)
    args = parser.parse_args()
    
    main(args)