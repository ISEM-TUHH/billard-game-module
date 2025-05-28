import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import socket
#import urllib.request
import requests
import json

def get_site_kp2(self):
		if request.method == "POST":
			return render_template("kp2.html")