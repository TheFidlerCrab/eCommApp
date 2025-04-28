import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import session
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text
