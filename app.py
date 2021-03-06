import os
from forms import  HomeForm, RolesForm, ComparisonForm, ConstructForm_Pos, ConstructForm_Neg, RatingForm
from flask import Flask, render_template, url_for, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from database import db_session
from database import Base
from models import SurveyData
from datetime import datetime
#from results import sample_chart
import pandas as pd
from io import StringIO
import base64
import matplotlib.pyplot as plt
import numpy.linalg as linalg
###################### Basic initialization of the app ###########################################
app = Flask(__name__)


# Key for Forms
app.config['SECRET_KEY'] = 'mysecret4key'

# Configuring the database path
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setting up the ability to migrate the database updates (keeping track of old fields and new field revisions)
migrate = Migrate(app, Base)

# Initializing a connection to the engine (to which we then make queries via our db_session)
from database import init_db
init_db()

# Import the data creation from the results module
from results import get_neg_handles, get_pos_handles, get_construct_names,\
get_people_names, get_ratings_matrix, get_self_ratings, make_loadings_matrix, make_targets_matrix
# Import the results displays
from results import loadings_describer, draw_loadings_heatmap, draw_targets_heatmap, draw_standing_charts

'''
# Enclosed here are some things I did to test adding and deleting users by a session. It will not work well because the fields
#have grown larger

# Looking at everything in database
test_get = SurveyData.query.all()
for u in test_get:
    print(u.role01, u.timestamp, u.rating_p15_const15, u.rating_p16_const15)

# Deleting all current users (useful for development!)
for u in test_get:
    db_session.delete(u)
print(test_get)
db_session.commit()
# Checking I deleted it all correctly
test_get2 = SurveyData.query.all()
print(test_get2)'''

# Below is the query that successfully returns the latest saved user. We use this often
#test_get = db_session.query(SurveyData).order_by(SurveyData.id.desc()).first()
# Checking the contents of test_get to ensure it has field attributes
#print(dir(test_get))
# Checking one of the db fields in the sample query
#print(test_get.oddgoose03)
# Checking that I did return the last row
#print('Ordering the database gives the final user role1 as {}'.format(test_get.role01))

############################################
        # VIEWS WITH FORMS
##########################################

''' This survey follows a pre-defined format in three phases.
Phase 1 - people list 15 people who have played significant roles in their life.
Phase 2 - people generate constructs after comparing triads of the fifteen roles. Each construct is generated as a text item.
Phase 3 - each person (role) is rated on all fifteen of the constructs.

Following the survey, the results are calculated.

Below is a list of survey pages in order. The main idea is that the data from each page
is stored in a session dictionary and called for subsequent pages. The questions are somewhat repetitive in structure
so the same template is rendered with new input data. This could probably be refactored in future iterations.
We then save all the results to a database after the last input page.

Results are presented after computation in a separate module using PCA, the elbow technique, and some basic interpretive rules.'''

timestamp = datetime.utcnow

##################### Defining the views ##############################################################

######## Start with a home page ####################################################
@app.route('/', methods=['GET','POST'])
def index():
    # Makes sure the current session is clear first
    session.clear()
    form = HomeForm()
    if request.method == 'POST':
        return redirect(url_for('roles'))
    return render_template('index.html', form=form)

############ Phase I - Role enumeration ############################################
@app.route('/roles', methods=['GET', 'POST'])
def roles():
    form = RolesForm()
    if form.validate_on_submit():
        session['role01'] = form.role01.data
        session['role02'] = form.role02.data
        session['role03'] = form.role03.data
        session['role04'] = form.role04.data
        session['role05'] = form.role05.data
        session['role06'] = form.role06.data
        session['role07'] = form.role07.data
        session['role08'] = form.role08.data
        session['role09'] = form.role09.data
        session['role10'] = form.role10.data
        session['role11'] = form.role11.data
        session['role12'] = form.role12.data
        session['role13'] = form.role13.data
        session['role14'] = form.role14.data
        session['role15'] = form.role15.data
        # adding bulk attributes the first time
        user = SurveyData(role01=session.get('role01'), role02=session.get('role02'), role03=session.get('role03'),
        role04=session.get('role04'), role05=session.get('role05'), role06=session.get('role06'), role07=session.get('role07'),
        role08=session.get('role08'), role09=session.get('role09'), role10=session.get('role10'), role11=session.get('role11'),
        role12=session.get('role12'), role13=session.get('role13'), role14=session.get('role14'), role15=session.get('role15'))
        db_session.add(user)
        db_session.commit()

        # This user_id call will be used throughout (I needed to generate it after the first commit)
        session['user_id'] = db_session.query(SurveyData).order_by(SurveyData.id.desc()).first().id

        return redirect(url_for('comparison1'))
    return render_template('roles2.html', form=form)

############## Phase II - Construct Generation #################################################################
# 2.1 ###################### Comparison set 1 (roles 10, 11, 12) ########################################

''' Only the first page is commented well, as the rest follow the same structure'''
@app.route('/comparison1', methods=['GET','POST'])
def comparison1():
    # Name the form we will use
    form = ComparisonForm()
    title = "Part II - Constructs (1 of 15)"
    # Update the data to print with the form
    form.oddoneout.choices = [('1', session.get('role10')), ('2', session.get('role11')), ('3', session.get('role12'))]
    # if the form is submitted
    if request.method == 'POST':
        # Save the form data to the session (NB NOT the db_session)
        session['oddgoose01'] = form.oddoneout.data
        # Update the database with new values
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose01':session['oddgoose01']})
        db_session.commit()
        # And move on to the next page
        return redirect(url_for('construct1_pos'))
    # show the form
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct1a', methods=['GET','POST'])
def construct1_pos():
    threeroles = [session.get('role10'), session.get('role11'), session.get('role12')]
    oddone = threeroles.pop(session.get('oddgoose01')-1) # Here I extract the name chosen on the previous page
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct1pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct1pos':session['construct1pos']})
        db_session.commit()
        return redirect(url_for('construct1_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct1b', methods=['GET','POST'])
def construct1_neg():
    pos_construct_to_feed = session['construct1pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct1neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct1neg':session['construct1neg']})
        db_session.commit()
        return redirect(url_for('comparison2'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.2 ############ Comparison Set 2 (roles 6, 13, 14) #####################################################
@app.route('/comparison2', methods=['GET','POST'])
def comparison2():
    form = ComparisonForm()
    title = "Part II - Constructs (2 of 15)"
    form.oddoneout.choices = [('1',session.get('role06')), ('2', session.get('role13')), ('3', session.get('role14'))]
    if request.method == 'POST':
        session['oddgoose02'] = form.oddoneout.data
        print(type(session.get('oddgoose02')))
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose01':session['oddgoose01']})
        db_session.commit()
        return redirect(url_for('construct2_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct2a', methods=['GET','POST'])
def construct2_pos():
    threeroles = [session.get('role06'), session.get('role13'), session.get('role14')]
    oddone = threeroles.pop(session.get('oddgoose02')-1)
    form = ConstructForm_Pos()
    if request.method == 'POST':
        session['construct2pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct2pos':session['construct2pos']})
        db_session.commit()
        return redirect(url_for('construct2_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct2b', methods=['GET','POST'])
def construct2_neg():
    pos_construct_to_feed = session['construct2pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct2neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct2neg':session['construct2neg']})
        db_session.commit()
        return redirect(url_for('comparison3'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.3 ############ Comparison Set 3 (roles 6, 9, 12) #####################################################
@app.route('/comparison3', methods=['GET','POST'])
def comparison3():
    form = ComparisonForm()
    title = "Part II - Constructs (3 of 15)"
    form.oddoneout.choices = [('1',session.get('role06')), ('2', session.get('role09')), ('3', session.get('role12'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose03'] = form.oddoneout.data
        print(type(session.get('oddgoose03')))
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose01':session['oddgoose03']})
        db_session.commit()
        return redirect(url_for('construct3_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct3a', methods=['GET','POST'])
def construct3_pos():
    threeroles = [session.get('role06'), session.get('role09'), session.get('role12')]
    oddone = threeroles.pop(session.get('oddgoose03')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct3pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct3pos':session['construct3pos']})
        db_session.commit()
        return redirect(url_for('construct3_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct3b', methods=['GET','POST'])
def construct3_neg():
    pos_construct_to_feed = session['construct3pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct3neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct3neg':session['construct3neg']})
        db_session.commit()
        return redirect(url_for('comparison4'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.4 ############ Comparison Set 4 (roles 3, 14, 15) #####################################################
@app.route('/comparison4', methods=['GET','POST'])
def comparison4():
    form = ComparisonForm()
    title = "Part II - Constructs (4 of 15)"
    form.oddoneout.choices = [('1',session.get('role03')), ('2', session.get('role14')), ('3', session.get('role15'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose04'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose04':session['oddgoose04']})
        db_session.commit()
        return redirect(url_for('construct4_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct4a', methods=['GET','POST'])
def construct4_pos():
    threeroles = [session.get('role03'), session.get('role14'), session.get('role15')]
    oddone = threeroles.pop(session.get('oddgoose04')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct4pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct4pos':session['construct4pos']})
        db_session.commit()
        return redirect(url_for('construct4_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct4b', methods=['GET','POST'])
def construct4_neg():
    pos_construct_to_feed = session['construct4pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct4neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct4neg':session['construct4neg']})
        db_session.commit()
        return redirect(url_for('comparison5'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.5 ############ Comparison Set 5 (roles 4, 11, 13) #####################################################
@app.route('/comparison5', methods=['GET','POST'])
def comparison5():
    form = ComparisonForm()
    title = "Part II - Constructs (5 of 15)"
    form.oddoneout.choices = [('1',session.get('role04')), ('2', session.get('role11')), ('3', session.get('role13'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose05'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose05':session['oddgoose05']})
        db_session.commit()
        return redirect(url_for('construct5_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct5a', methods=['GET','POST'])
def construct5_pos():
    threeroles = [session.get('role04'), session.get('role11'), session.get('role13')]
    oddone = threeroles.pop(session.get('oddgoose05')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct5pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct5pos':session['construct5pos']})
        db_session.commit()
        return redirect(url_for('construct5_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct5b', methods=['GET','POST'])
def construct5_neg():
    pos_construct_to_feed = session['construct5pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct5neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct5neg':session['construct5neg']})
        db_session.commit()
        return redirect(url_for('comparison6'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.6 ############ Comparison Set 6 (roles 2, 9, 10) #####################################################
@app.route('/comparison6', methods=['GET','POST'])
def comparison6():
    form = ComparisonForm()
    title = "Part II - Constructs (6 of 15)"
    form.oddoneout.choices = [('1',session.get('role02')), ('2', session.get('role09')), ('3', session.get('role10'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose06'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose06':session['oddgoose06']})
        db_session.commit()
        return redirect(url_for('construct6_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct6a', methods=['GET','POST'])
def construct6_pos():
    threeroles = [session.get('role02'), session.get('role09'), session.get('role10')]
    oddone = threeroles.pop(session.get('oddgoose06')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct6pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct6pos':session['construct6pos']})
        db_session.commit()
        return redirect(url_for('construct6_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct6b', methods=['GET','POST'])
def construct6_neg():
    pos_construct_to_feed = session['construct6pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct6neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct6neg':session['construct6neg']})
        db_session.commit()
        return redirect(url_for('comparison7'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.7 ############ Comparison Set 7 (roles 5, 7, 8) #####################################################
@app.route('/comparison7', methods=['GET','POST'])
def comparison7():
    form = ComparisonForm()
    title = "Part II - Constructs (7 of 15)"
    form.oddoneout.choices = [('1',session.get('role05')), ('2', session.get('role07')), ('3', session.get('role08'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose07'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose07':session['oddgoose07']})
        db_session.commit()
        return redirect(url_for('construct7_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct7a', methods=['GET','POST'])
def construct7_pos():
    threeroles = [session.get('role05'), session.get('role07'), session.get('role08')]
    oddone = threeroles.pop(session.get('oddgoose07')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct7pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct7pos':session['construct7pos']})
        db_session.commit()
        return redirect(url_for('construct7_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct7b', methods=['GET','POST'])
def construct7_neg():
    pos_construct_to_feed = session['construct7pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct7neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct7neg':session['construct7neg']})
        db_session.commit()
        return redirect(url_for('comparison8'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.8 ############ Comparison Set 8 (roles 9, 11, 15) #####################################################
@app.route('/comparison8', methods=['GET','POST'])
def comparison8():
    form = ComparisonForm()
    title = "Part II - Constructs (8 of 15)"
    form.oddoneout.choices = [('1',session.get('role09')), ('2', session.get('role11')), ('3', session.get('role15'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose08'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose08':session['oddgoose08']})
        db_session.commit()
        return redirect(url_for('construct8_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct8a', methods=['GET','POST'])
def construct8_pos():
    threeroles = [session.get('role09'), session.get('role11'), session.get('role15')]
    oddone = threeroles.pop(session.get('oddgoose08')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct8pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct8pos':session['construct8pos']})
        db_session.commit()
        return redirect(url_for('construct8_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct8b', methods=['GET','POST'])
def construct8_neg():
    pos_construct_to_feed = session['construct8pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct8neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct8neg':session['construct8neg']})
        db_session.commit()
        return redirect(url_for('comparison9'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.9 ############ Comparison Set 9 (roles 1, 4, 7) #####################################################
@app.route('/comparison9', methods=['GET','POST'])
def comparison9():
    form = ComparisonForm()
    title = "Part II - Constructs (9 of 15)"
    form.oddoneout.choices = [('1',session.get('role01')), ('2', session.get('role04')), ('3', session.get('role07'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose09'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose09':session['oddgoose09']})
        db_session.commit()
        return redirect(url_for('construct9_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct9a', methods=['GET','POST'])
def construct9_pos():
    threeroles = [session.get('role01'), session.get('role04'), session.get('role07')]
    oddone = threeroles.pop(session.get('oddgoose09')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct9pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct9pos':session['construct9pos']})
        db_session.commit()
        return redirect(url_for('construct9_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct9b', methods=['GET','POST'])
def construct9_neg():
    pos_construct_to_feed = session['construct9pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct9neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct9neg':session['construct9neg']})
        db_session.commit()
        return redirect(url_for('comparison10'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.10 ############ Comparison Set 10 (roles 3, 5, 13) #####################################################
@app.route('/comparison10', methods=['GET','POST'])
def comparison10():
    form = ComparisonForm()
    title = "Part II - Constructs (10 of 15)"
    form.oddoneout.choices = [('1',session.get('role03')), ('2', session.get('role05')), ('3', session.get('role13'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose10'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose10':session['oddgoose10']})
        db_session.commit()
        return redirect(url_for('construct10_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct10a', methods=['GET','POST'])
def construct10_pos():
    threeroles = [session.get('role03'), session.get('role05'), session.get('role13')]
    oddone = threeroles.pop(session.get('oddgoose10')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct10pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct10pos':session['construct10pos']})
        db_session.commit()
        return redirect(url_for('construct10_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct10b', methods=['GET','POST'])
def construct10_neg():
    pos_construct_to_feed = session['construct10pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct10neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct10neg':session['construct10neg']})
        db_session.commit()
        return redirect(url_for('comparison11'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.11 ############ Comparison Set 11 (roles 8, 12, 14) #####################################################
@app.route('/comparison11', methods=['GET','POST'])
def comparison11():
    form = ComparisonForm()
    title = "Part II - Constructs (11 of 15)"
    form.oddoneout.choices = [('1',session.get('role08')), ('2', session.get('role12')), ('3', session.get('role14'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose11'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose11':session['oddgoose11']})
        db_session.commit()
        return redirect(url_for('construct11_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct11a', methods=['GET','POST'])
def construct11_pos():
    threeroles = [session.get('role08'), session.get('role12'), session.get('role14')]
    oddone = threeroles.pop(session.get('oddgoose11')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct11pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct11pos':session['construct11pos']})
        db_session.commit()
        return redirect(url_for('construct11_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct11b', methods=['GET','POST'])
def construct11_neg():
    pos_construct_to_feed = session['construct11pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct11neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct11neg':session['construct11neg']})
        db_session.commit()
        return redirect(url_for('comparison12'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.12 ############ Comparison Set 12 (roles 4, 5, 15) #####################################################
@app.route('/comparison12', methods=['GET','POST'])
def comparison12():
    form = ComparisonForm()
    title = "Part II - Constructs (12 of 15)"
    form.oddoneout.choices = [('1',session.get('role04')), ('2', session.get('role05')), ('3', session.get('role15'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose12'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose12':session['oddgoose12']})
        db_session.commit()
        return redirect(url_for('construct12_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct12a', methods=['GET','POST'])
def construct12_pos():
    threeroles = [session.get('role04'), session.get('role05'), session.get('role15')]
    oddone = threeroles.pop(session.get('oddgoose12')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct12pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct12pos':session['construct12pos']})
        db_session.commit()
        return redirect(url_for('construct12_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct12b', methods=['GET','POST'])
def construct12_neg():
    pos_construct_to_feed = session['construct12pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct12neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct12neg':session['construct12neg']})
        db_session.commit()
        return redirect(url_for('comparison13'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.13 ############ Comparison Set 13 (roles 1, 2, 8) #####################################################
@app.route('/comparison13', methods=['GET','POST'])
def comparison13():
    form = ComparisonForm()
    title = "Part II - Constructs (13 of 15)"
    form.oddoneout.choices = [('1',session.get('role01')), ('2', session.get('role02')), ('3', session.get('role08'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose13'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose13':session['oddgoose13']})
        db_session.commit()
        return redirect(url_for('construct13_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct13a', methods=['GET','POST'])
def construct13_pos():
    threeroles = [session.get('role01'), session.get('role02'), session.get('role08')]
    oddone = threeroles.pop(session.get('oddgoose13')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct13pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct13pos':session['construct13pos']})
        db_session.commit()
        return redirect(url_for('construct13_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct13b', methods=['GET','POST'])
def construct13_neg():
    pos_construct_to_feed = session['construct13pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct13neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct13neg':session['construct13neg']})
        db_session.commit()
        return redirect(url_for('comparison14'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.14 ############ Comparison Set 14 (roles 2, 3, 7) #####################################################
@app.route('/comparison14', methods=['GET','POST'])
def comparison14():
    form = ComparisonForm()
    title = "Part II - Constructs (14 of 15)"
    form.oddoneout.choices = [('1',session.get('role02')), ('2', session.get('role03')), ('3', session.get('role07'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose14'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose14':session['oddgoose14']})
        db_session.commit()
        return redirect(url_for('construct14_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct14a', methods=['GET','POST'])
def construct14_pos():
    threeroles = [session.get('role02'), session.get('role03'), session.get('role07')]
    oddone = threeroles.pop(session.get('oddgoose14')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct14pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct14pos':session['construct14pos']})
        db_session.commit()
        return redirect(url_for('construct14_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct14b', methods=['GET','POST'])
def construct14_neg():
    pos_construct_to_feed = session['construct14pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct14neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct14neg':session['construct14neg']})
        db_session.commit()
        return redirect(url_for('comparison15'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 2.14 ############ Comparison Set 15 (roles 1, 6, 10) #####################################################
@app.route('/comparison15', methods=['GET','POST'])
def comparison15():
    form = ComparisonForm()
    title = "Part II - Constructs (15 of 15)"
    form.oddoneout.choices = [('1',session.get('role01')), ('2', session.get('role06')), ('3', session.get('role10'))]
    if request.method == 'POST':    #validate_on_submit()
        session['oddgoose15'] = form.oddoneout.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'oddgoose15':session['oddgoose15']})
        db_session.commit()
        return redirect(url_for('construct15_pos'))
    return render_template('comparisons.html', title=title, form=form)

@app.route('/construct15a', methods=['GET','POST'])
def construct15_pos():
    threeroles = [session.get('role01'), session.get('role06'), session.get('role10')]
    oddone = threeroles.pop(session.get('oddgoose15')-1)
    form = ConstructForm_Pos()
    if form.validate_on_submit():
        session['construct15pos'] = form.positive_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct15pos':session['construct15pos']})
        db_session.commit()
        return redirect(url_for('construct15_neg'))
    return render_template('construct_pos.html', form=form, oddone=oddone, threeroles=threeroles)

@app.route('/construct15b', methods=['GET','POST'])
def construct15_neg():
    pos_construct_to_feed = session['construct15pos']
    form = ConstructForm_Neg()
    if request.method == 'POST':
        session['construct15neg'] = form.negative_construct_pole.data
        db_session.query(SurveyData).filter_by(id=session['user_id']).update({'construct15neg':session['construct15neg']})
        db_session.commit()
        return redirect(url_for('rating_instructions'))
    return render_template('construct_neg.html', form=form, pos_construct_to_feed=pos_construct_to_feed)

# 3 ################## Phase 3 - Rating of roles on constructs ##################################################

@app.route('/ratings_instructions', methods=['GET', 'POST'])
def rating_instructions():
    form = HomeForm()
    if request.method == 'POST':
        return redirect(url_for('ratings1'))
    return render_template('ratings_instructions.html', form=form)

@app.route('/ratings/1', methods=['GET', 'POST'])
def ratings1():
    target = session.get('role01') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p1_const1'] = form.rating_const1.data
        session['rating_p1_const2'] = form.rating_const2.data
        session['rating_p1_const3'] = form.rating_const3.data
        session['rating_p1_const4'] = form.rating_const4.data
        session['rating_p1_const5'] = form.rating_const5.data
        session['rating_p1_const6'] = form.rating_const6.data
        session['rating_p1_const7'] = form.rating_const7.data
        session['rating_p1_const8'] = form.rating_const8.data
        session['rating_p1_const9'] = form.rating_const9.data
        session['rating_p1_const10'] = form.rating_const10.data
        session['rating_p1_const11'] = form.rating_const11.data
        session['rating_p1_const12'] = form.rating_const12.data
        session['rating_p1_const13'] = form.rating_const13.data
        session['rating_p1_const14'] = form.rating_const14.data
        session['rating_p1_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p1_const1': form.rating_const1.data,
        'rating_p1_const2': form.rating_const2.data,
        'rating_p1_const3': form.rating_const3.data,
        'rating_p1_const4': form.rating_const4.data,
        'rating_p1_const5': form.rating_const5.data,
        'rating_p1_const6': form.rating_const6.data,
        'rating_p1_const7': form.rating_const7.data,
        'rating_p1_const8': form.rating_const8.data,
        'rating_p1_const9': form.rating_const9.data,
        'rating_p1_const10': form.rating_const10.data,
        'rating_p1_const11': form.rating_const11.data,
        'rating_p1_const12': form.rating_const12.data,
        'rating_p1_const13': form.rating_const13.data,
        'rating_p1_const14': form.rating_const14.data,
        'rating_p1_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings2'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/2', methods=['GET', 'POST'])
def ratings2():
    target = session.get('role02') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p2_const1'] = form.rating_const1.data
        session['rating_p2_const2'] = form.rating_const2.data
        session['rating_p2_const3'] = form.rating_const3.data
        session['rating_p2_const4'] = form.rating_const4.data
        session['rating_p2_const5'] = form.rating_const5.data
        session['rating_p2_const6'] = form.rating_const6.data
        session['rating_p2_const7'] = form.rating_const7.data
        session['rating_p2_const8'] = form.rating_const8.data
        session['rating_p2_const9'] = form.rating_const9.data
        session['rating_p2_const10'] = form.rating_const10.data
        session['rating_p2_const11'] = form.rating_const11.data
        session['rating_p2_const12'] = form.rating_const12.data
        session['rating_p2_const13'] = form.rating_const13.data
        session['rating_p2_const14'] = form.rating_const14.data
        session['rating_p2_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p2_const1': form.rating_const1.data,
        'rating_p2_const2': form.rating_const2.data,
        'rating_p2_const3': form.rating_const3.data,
        'rating_p2_const4': form.rating_const4.data,
        'rating_p2_const5': form.rating_const5.data,
        'rating_p2_const6': form.rating_const6.data,
        'rating_p2_const7': form.rating_const7.data,
        'rating_p2_const8': form.rating_const8.data,
        'rating_p2_const9': form.rating_const9.data,
        'rating_p2_const10': form.rating_const10.data,
        'rating_p2_const11': form.rating_const11.data,
        'rating_p2_const12': form.rating_const12.data,
        'rating_p2_const13': form.rating_const13.data,
        'rating_p2_const14': form.rating_const14.data,
        'rating_p2_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings3'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/3', methods=['GET', 'POST'])
def ratings3():
    target = session.get('role03') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p3_const1'] = form.rating_const1.data
        session['rating_p3_const2'] = form.rating_const2.data
        session['rating_p3_const3'] = form.rating_const3.data
        session['rating_p3_const4'] = form.rating_const4.data
        session['rating_p3_const5'] = form.rating_const5.data
        session['rating_p3_const6'] = form.rating_const6.data
        session['rating_p3_const7'] = form.rating_const7.data
        session['rating_p3_const8'] = form.rating_const8.data
        session['rating_p3_const9'] = form.rating_const9.data
        session['rating_p3_const10'] = form.rating_const10.data
        session['rating_p3_const11'] = form.rating_const11.data
        session['rating_p3_const12'] = form.rating_const12.data
        session['rating_p3_const13'] = form.rating_const13.data
        session['rating_p3_const14'] = form.rating_const14.data
        session['rating_p3_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p3_const1': form.rating_const1.data,
        'rating_p3_const2': form.rating_const2.data,
        'rating_p3_const3': form.rating_const3.data,
        'rating_p3_const4': form.rating_const4.data,
        'rating_p3_const5': form.rating_const5.data,
        'rating_p3_const6': form.rating_const6.data,
        'rating_p3_const7': form.rating_const7.data,
        'rating_p3_const8': form.rating_const8.data,
        'rating_p3_const9': form.rating_const9.data,
        'rating_p3_const10': form.rating_const10.data,
        'rating_p3_const11': form.rating_const11.data,
        'rating_p3_const12': form.rating_const12.data,
        'rating_p3_const13': form.rating_const13.data,
        'rating_p3_const14': form.rating_const14.data,
        'rating_p3_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings4'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/4', methods=['GET', 'POST'])
def ratings4():
    target = session.get('role04') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p4_const1'] = form.rating_const1.data
        session['rating_p4_const2'] = form.rating_const2.data
        session['rating_p4_const3'] = form.rating_const3.data
        session['rating_p4_const4'] = form.rating_const4.data
        session['rating_p4_const5'] = form.rating_const5.data
        session['rating_p4_const6'] = form.rating_const6.data
        session['rating_p4_const7'] = form.rating_const7.data
        session['rating_p4_const8'] = form.rating_const8.data
        session['rating_p4_const9'] = form.rating_const9.data
        session['rating_p4_const10'] = form.rating_const10.data
        session['rating_p4_const11'] = form.rating_const11.data
        session['rating_p4_const12'] = form.rating_const12.data
        session['rating_p4_const13'] = form.rating_const13.data
        session['rating_p4_const14'] = form.rating_const14.data
        session['rating_p4_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p4_const1': form.rating_const1.data,
        'rating_p4_const2': form.rating_const2.data,
        'rating_p4_const3': form.rating_const3.data,
        'rating_p4_const4': form.rating_const4.data,
        'rating_p4_const5': form.rating_const5.data,
        'rating_p4_const6': form.rating_const6.data,
        'rating_p4_const7': form.rating_const7.data,
        'rating_p4_const8': form.rating_const8.data,
        'rating_p4_const9': form.rating_const9.data,
        'rating_p4_const10': form.rating_const10.data,
        'rating_p4_const11': form.rating_const11.data,
        'rating_p4_const12': form.rating_const12.data,
        'rating_p4_const13': form.rating_const13.data,
        'rating_p4_const14': form.rating_const14.data,
        'rating_p4_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings5'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/5', methods=['GET', 'POST'])
def ratings5():
    target = session.get('role05') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p5_const1'] = form.rating_const1.data
        session['rating_p5_const2'] = form.rating_const2.data
        session['rating_p5_const3'] = form.rating_const3.data
        session['rating_p5_const4'] = form.rating_const4.data
        session['rating_p5_const5'] = form.rating_const5.data
        session['rating_p5_const6'] = form.rating_const6.data
        session['rating_p5_const7'] = form.rating_const7.data
        session['rating_p5_const8'] = form.rating_const8.data
        session['rating_p5_const9'] = form.rating_const9.data
        session['rating_p5_const10'] = form.rating_const10.data
        session['rating_p5_const11'] = form.rating_const11.data
        session['rating_p5_const12'] = form.rating_const12.data
        session['rating_p5_const13'] = form.rating_const13.data
        session['rating_p5_const14'] = form.rating_const14.data
        session['rating_p5_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p5_const1': form.rating_const1.data,
        'rating_p5_const2': form.rating_const2.data,
        'rating_p5_const3': form.rating_const3.data,
        'rating_p5_const4': form.rating_const4.data,
        'rating_p5_const5': form.rating_const5.data,
        'rating_p5_const6': form.rating_const6.data,
        'rating_p5_const7': form.rating_const7.data,
        'rating_p5_const8': form.rating_const8.data,
        'rating_p5_const9': form.rating_const9.data,
        'rating_p5_const10': form.rating_const10.data,
        'rating_p5_const11': form.rating_const11.data,
        'rating_p5_const12': form.rating_const12.data,
        'rating_p5_const13': form.rating_const13.data,
        'rating_p5_const14': form.rating_const14.data,
        'rating_p5_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings6'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/6', methods=['GET', 'POST'])
def ratings6():
    target = session.get('role06') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p6_const1'] = form.rating_const1.data
        session['rating_p6_const2'] = form.rating_const2.data
        session['rating_p6_const3'] = form.rating_const3.data
        session['rating_p6_const4'] = form.rating_const4.data
        session['rating_p6_const5'] = form.rating_const5.data
        session['rating_p6_const6'] = form.rating_const6.data
        session['rating_p6_const7'] = form.rating_const7.data
        session['rating_p6_const8'] = form.rating_const8.data
        session['rating_p6_const9'] = form.rating_const9.data
        session['rating_p6_const10'] = form.rating_const10.data
        session['rating_p6_const11'] = form.rating_const11.data
        session['rating_p6_const12'] = form.rating_const12.data
        session['rating_p6_const13'] = form.rating_const13.data
        session['rating_p6_const14'] = form.rating_const14.data
        session['rating_p6_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p6_const1': form.rating_const1.data,
        'rating_p6_const2': form.rating_const2.data,
        'rating_p6_const3': form.rating_const3.data,
        'rating_p6_const4': form.rating_const4.data,
        'rating_p6_const5': form.rating_const5.data,
        'rating_p6_const6': form.rating_const6.data,
        'rating_p6_const7': form.rating_const7.data,
        'rating_p6_const8': form.rating_const8.data,
        'rating_p6_const9': form.rating_const9.data,
        'rating_p6_const10': form.rating_const10.data,
        'rating_p6_const11': form.rating_const11.data,
        'rating_p6_const12': form.rating_const12.data,
        'rating_p6_const13': form.rating_const13.data,
        'rating_p6_const14': form.rating_const14.data,
        'rating_p6_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings7'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/7', methods=['GET', 'POST'])
def ratings7():
    target = session.get('role07') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p7_const1'] = form.rating_const1.data
        session['rating_p7_const2'] = form.rating_const2.data
        session['rating_p7_const3'] = form.rating_const3.data
        session['rating_p7_const4'] = form.rating_const4.data
        session['rating_p7_const5'] = form.rating_const5.data
        session['rating_p7_const6'] = form.rating_const6.data
        session['rating_p7_const7'] = form.rating_const7.data
        session['rating_p7_const8'] = form.rating_const8.data
        session['rating_p7_const9'] = form.rating_const9.data
        session['rating_p7_const10'] = form.rating_const10.data
        session['rating_p7_const11'] = form.rating_const11.data
        session['rating_p7_const12'] = form.rating_const12.data
        session['rating_p7_const13'] = form.rating_const13.data
        session['rating_p7_const14'] = form.rating_const14.data
        session['rating_p7_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p7_const1': form.rating_const1.data,
        'rating_p7_const2': form.rating_const2.data,
        'rating_p7_const3': form.rating_const3.data,
        'rating_p7_const4': form.rating_const4.data,
        'rating_p7_const5': form.rating_const5.data,
        'rating_p7_const6': form.rating_const6.data,
        'rating_p7_const7': form.rating_const7.data,
        'rating_p7_const8': form.rating_const8.data,
        'rating_p7_const9': form.rating_const9.data,
        'rating_p7_const10': form.rating_const10.data,
        'rating_p7_const11': form.rating_const11.data,
        'rating_p7_const12': form.rating_const12.data,
        'rating_p7_const13': form.rating_const13.data,
        'rating_p7_const14': form.rating_const14.data,
        'rating_p7_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings8'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/8', methods=['GET', 'POST'])
def ratings8():
    target = session.get('role08') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p8_const1'] = form.rating_const1.data
        session['rating_p8_const2'] = form.rating_const2.data
        session['rating_p8_const3'] = form.rating_const3.data
        session['rating_p8_const4'] = form.rating_const4.data
        session['rating_p8_const5'] = form.rating_const5.data
        session['rating_p8_const6'] = form.rating_const6.data
        session['rating_p8_const7'] = form.rating_const7.data
        session['rating_p8_const8'] = form.rating_const8.data
        session['rating_p8_const9'] = form.rating_const9.data
        session['rating_p8_const10'] = form.rating_const10.data
        session['rating_p8_const11'] = form.rating_const11.data
        session['rating_p8_const12'] = form.rating_const12.data
        session['rating_p8_const13'] = form.rating_const13.data
        session['rating_p8_const14'] = form.rating_const14.data
        session['rating_p8_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p8_const1': form.rating_const1.data,
        'rating_p8_const2': form.rating_const2.data,
        'rating_p8_const3': form.rating_const3.data,
        'rating_p8_const4': form.rating_const4.data,
        'rating_p8_const5': form.rating_const5.data,
        'rating_p8_const6': form.rating_const6.data,
        'rating_p8_const7': form.rating_const7.data,
        'rating_p8_const8': form.rating_const8.data,
        'rating_p8_const9': form.rating_const9.data,
        'rating_p8_const10': form.rating_const10.data,
        'rating_p8_const11': form.rating_const11.data,
        'rating_p8_const12': form.rating_const12.data,
        'rating_p8_const13': form.rating_const13.data,
        'rating_p8_const14': form.rating_const14.data,
        'rating_p8_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings9'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/9', methods=['GET', 'POST'])
def ratings9():
    target = session.get('role09') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p9_const1'] = form.rating_const1.data
        session['rating_p9_const2'] = form.rating_const2.data
        session['rating_p9_const3'] = form.rating_const3.data
        session['rating_p9_const4'] = form.rating_const4.data
        session['rating_p9_const5'] = form.rating_const5.data
        session['rating_p9_const6'] = form.rating_const6.data
        session['rating_p9_const7'] = form.rating_const7.data
        session['rating_p9_const8'] = form.rating_const8.data
        session['rating_p9_const9'] = form.rating_const9.data
        session['rating_p9_const10'] = form.rating_const10.data
        session['rating_p9_const11'] = form.rating_const11.data
        session['rating_p9_const12'] = form.rating_const12.data
        session['rating_p9_const13'] = form.rating_const13.data
        session['rating_p9_const14'] = form.rating_const14.data
        session['rating_p9_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p9_const1': form.rating_const1.data,
        'rating_p9_const2': form.rating_const2.data,
        'rating_p9_const3': form.rating_const3.data,
        'rating_p9_const4': form.rating_const4.data,
        'rating_p9_const5': form.rating_const5.data,
        'rating_p9_const6': form.rating_const6.data,
        'rating_p9_const7': form.rating_const7.data,
        'rating_p9_const8': form.rating_const8.data,
        'rating_p9_const9': form.rating_const9.data,
        'rating_p9_const10': form.rating_const10.data,
        'rating_p9_const11': form.rating_const11.data,
        'rating_p9_const12': form.rating_const12.data,
        'rating_p9_const13': form.rating_const13.data,
        'rating_p9_const14': form.rating_const14.data,
        'rating_p9_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings10'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/10', methods=['GET', 'POST'])
def ratings10():
    target = session.get('role10') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p10_const1'] = form.rating_const1.data
        session['rating_p10_const2'] = form.rating_const2.data
        session['rating_p10_const3'] = form.rating_const3.data
        session['rating_p10_const4'] = form.rating_const4.data
        session['rating_p10_const5'] = form.rating_const5.data
        session['rating_p10_const6'] = form.rating_const6.data
        session['rating_p10_const7'] = form.rating_const7.data
        session['rating_p10_const8'] = form.rating_const8.data
        session['rating_p10_const9'] = form.rating_const9.data
        session['rating_p10_const10'] = form.rating_const10.data
        session['rating_p10_const11'] = form.rating_const11.data
        session['rating_p10_const12'] = form.rating_const12.data
        session['rating_p10_const13'] = form.rating_const13.data
        session['rating_p10_const14'] = form.rating_const14.data
        session['rating_p10_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p10_const1': form.rating_const1.data,
        'rating_p10_const2': form.rating_const2.data,
        'rating_p10_const3': form.rating_const3.data,
        'rating_p10_const4': form.rating_const4.data,
        'rating_p10_const5': form.rating_const5.data,
        'rating_p10_const6': form.rating_const6.data,
        'rating_p10_const7': form.rating_const7.data,
        'rating_p10_const8': form.rating_const8.data,
        'rating_p10_const9': form.rating_const9.data,
        'rating_p10_const10': form.rating_const10.data,
        'rating_p10_const11': form.rating_const11.data,
        'rating_p10_const12': form.rating_const12.data,
        'rating_p10_const13': form.rating_const13.data,
        'rating_p10_const14': form.rating_const14.data,
        'rating_p10_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings11'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/11', methods=['GET', 'POST'])
def ratings11():
    target = session.get('role11') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p11_const1'] = form.rating_const1.data
        session['rating_p11_const2'] = form.rating_const2.data
        session['rating_p11_const3'] = form.rating_const3.data
        session['rating_p11_const4'] = form.rating_const4.data
        session['rating_p11_const5'] = form.rating_const5.data
        session['rating_p11_const6'] = form.rating_const6.data
        session['rating_p11_const7'] = form.rating_const7.data
        session['rating_p11_const8'] = form.rating_const8.data
        session['rating_p11_const9'] = form.rating_const9.data
        session['rating_p11_const10'] = form.rating_const10.data
        session['rating_p11_const11'] = form.rating_const11.data
        session['rating_p11_const12'] = form.rating_const12.data
        session['rating_p11_const13'] = form.rating_const13.data
        session['rating_p11_const14'] = form.rating_const14.data
        session['rating_p11_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p11_const1': form.rating_const1.data,
        'rating_p11_const2': form.rating_const2.data,
        'rating_p11_const3': form.rating_const3.data,
        'rating_p11_const4': form.rating_const4.data,
        'rating_p11_const5': form.rating_const5.data,
        'rating_p11_const6': form.rating_const6.data,
        'rating_p11_const7': form.rating_const7.data,
        'rating_p11_const8': form.rating_const8.data,
        'rating_p11_const9': form.rating_const9.data,
        'rating_p11_const10': form.rating_const10.data,
        'rating_p11_const11': form.rating_const11.data,
        'rating_p11_const12': form.rating_const12.data,
        'rating_p11_const13': form.rating_const13.data,
        'rating_p11_const14': form.rating_const14.data,
        'rating_p11_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings12'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/12', methods=['GET', 'POST'])
def ratings12():
    target = session.get('role12') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p12_const1'] = form.rating_const1.data
        session['rating_p12_const2'] = form.rating_const2.data
        session['rating_p12_const3'] = form.rating_const3.data
        session['rating_p12_const4'] = form.rating_const4.data
        session['rating_p12_const5'] = form.rating_const5.data
        session['rating_p12_const6'] = form.rating_const6.data
        session['rating_p12_const7'] = form.rating_const7.data
        session['rating_p12_const8'] = form.rating_const8.data
        session['rating_p12_const9'] = form.rating_const9.data
        session['rating_p12_const10'] = form.rating_const10.data
        session['rating_p12_const11'] = form.rating_const11.data
        session['rating_p12_const12'] = form.rating_const12.data
        session['rating_p12_const13'] = form.rating_const13.data
        session['rating_p12_const14'] = form.rating_const14.data
        session['rating_p12_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p12_const1': form.rating_const1.data,
        'rating_p12_const2': form.rating_const2.data,
        'rating_p12_const3': form.rating_const3.data,
        'rating_p12_const4': form.rating_const4.data,
        'rating_p12_const5': form.rating_const5.data,
        'rating_p12_const6': form.rating_const6.data,
        'rating_p12_const7': form.rating_const7.data,
        'rating_p12_const8': form.rating_const8.data,
        'rating_p12_const9': form.rating_const9.data,
        'rating_p12_const10': form.rating_const10.data,
        'rating_p12_const11': form.rating_const11.data,
        'rating_p12_const12': form.rating_const12.data,
        'rating_p12_const13': form.rating_const13.data,
        'rating_p12_const14': form.rating_const14.data,
        'rating_p12_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings13'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/13', methods=['GET', 'POST'])
def ratings13():
    target = session.get('role13') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p13_const1'] = form.rating_const1.data
        session['rating_p13_const2'] = form.rating_const2.data
        session['rating_p13_const3'] = form.rating_const3.data
        session['rating_p13_const4'] = form.rating_const4.data
        session['rating_p13_const5'] = form.rating_const5.data
        session['rating_p13_const6'] = form.rating_const6.data
        session['rating_p13_const7'] = form.rating_const7.data
        session['rating_p13_const8'] = form.rating_const8.data
        session['rating_p13_const9'] = form.rating_const9.data
        session['rating_p13_const10'] = form.rating_const10.data
        session['rating_p13_const11'] = form.rating_const11.data
        session['rating_p13_const12'] = form.rating_const12.data
        session['rating_p13_const13'] = form.rating_const13.data
        session['rating_p13_const14'] = form.rating_const14.data
        session['rating_p13_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p13_const1': form.rating_const1.data,
        'rating_p13_const2': form.rating_const2.data,
        'rating_p13_const3': form.rating_const3.data,
        'rating_p13_const4': form.rating_const4.data,
        'rating_p13_const5': form.rating_const5.data,
        'rating_p13_const6': form.rating_const6.data,
        'rating_p13_const7': form.rating_const7.data,
        'rating_p13_const8': form.rating_const8.data,
        'rating_p13_const9': form.rating_const9.data,
        'rating_p13_const10': form.rating_const10.data,
        'rating_p13_const11': form.rating_const11.data,
        'rating_p13_const12': form.rating_const12.data,
        'rating_p13_const13': form.rating_const13.data,
        'rating_p13_const14': form.rating_const14.data,
        'rating_p13_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings14'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/14', methods=['GET', 'POST'])
def ratings14():
    target = session.get('role14') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p14_const1'] = form.rating_const1.data
        session['rating_p14_const2'] = form.rating_const2.data
        session['rating_p14_const3'] = form.rating_const3.data
        session['rating_p14_const4'] = form.rating_const4.data
        session['rating_p14_const5'] = form.rating_const5.data
        session['rating_p14_const6'] = form.rating_const6.data
        session['rating_p14_const7'] = form.rating_const7.data
        session['rating_p14_const8'] = form.rating_const8.data
        session['rating_p14_const9'] = form.rating_const9.data
        session['rating_p14_const10'] = form.rating_const10.data
        session['rating_p14_const11'] = form.rating_const11.data
        session['rating_p14_const12'] = form.rating_const12.data
        session['rating_p14_const13'] = form.rating_const13.data
        session['rating_p14_const14'] = form.rating_const14.data
        session['rating_p14_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p14_const1': form.rating_const1.data,
        'rating_p14_const2': form.rating_const2.data,
        'rating_p14_const3': form.rating_const3.data,
        'rating_p14_const4': form.rating_const4.data,
        'rating_p14_const5': form.rating_const5.data,
        'rating_p14_const6': form.rating_const6.data,
        'rating_p14_const7': form.rating_const7.data,
        'rating_p14_const8': form.rating_const8.data,
        'rating_p14_const9': form.rating_const9.data,
        'rating_p14_const10': form.rating_const10.data,
        'rating_p14_const11': form.rating_const11.data,
        'rating_p14_const12': form.rating_const12.data,
        'rating_p14_const13': form.rating_const13.data,
        'rating_p14_const14': form.rating_const14.data,
        'rating_p14_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings15'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/15', methods=['GET', 'POST'])
def ratings15():
    target = session.get('role15') # getting the new role
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p15_const1'] = form.rating_const1.data
        session['rating_p15_const2'] = form.rating_const2.data
        session['rating_p15_const3'] = form.rating_const3.data
        session['rating_p15_const4'] = form.rating_const4.data
        session['rating_p15_const5'] = form.rating_const5.data
        session['rating_p15_const6'] = form.rating_const6.data
        session['rating_p15_const7'] = form.rating_const7.data
        session['rating_p15_const8'] = form.rating_const8.data
        session['rating_p15_const9'] = form.rating_const9.data
        session['rating_p15_const10'] = form.rating_const10.data
        session['rating_p15_const11'] = form.rating_const11.data
        session['rating_p15_const12'] = form.rating_const12.data
        session['rating_p15_const13'] = form.rating_const13.data
        session['rating_p15_const14'] = form.rating_const14.data
        session['rating_p15_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p15_const1': form.rating_const1.data,
        'rating_p15_const2': form.rating_const2.data,
        'rating_p15_const3': form.rating_const3.data,
        'rating_p15_const4': form.rating_const4.data,
        'rating_p15_const5': form.rating_const5.data,
        'rating_p15_const6': form.rating_const6.data,
        'rating_p15_const7': form.rating_const7.data,
        'rating_p15_const8': form.rating_const8.data,
        'rating_p15_const9': form.rating_const9.data,
        'rating_p15_const10': form.rating_const10.data,
        'rating_p15_const11': form.rating_const11.data,
        'rating_p15_const12': form.rating_const12.data,
        'rating_p15_const13': form.rating_const13.data,
        'rating_p15_const14': form.rating_const14.data,
        'rating_p15_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('ratings16'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

@app.route('/ratings/16', methods=['GET', 'POST'])
def ratings16():
    target = 'Yourself'
    form = RatingForm()
    if request.method == 'POST':
        # saving form data as session variables
        session['rating_p16_const1'] = form.rating_const1.data
        session['rating_p16_const2'] = form.rating_const2.data
        session['rating_p16_const3'] = form.rating_const3.data
        session['rating_p16_const4'] = form.rating_const4.data
        session['rating_p16_const5'] = form.rating_const5.data
        session['rating_p16_const6'] = form.rating_const6.data
        session['rating_p16_const7'] = form.rating_const7.data
        session['rating_p16_const8'] = form.rating_const8.data
        session['rating_p16_const9'] = form.rating_const9.data
        session['rating_p16_const10'] = form.rating_const10.data
        session['rating_p16_const11'] = form.rating_const11.data
        session['rating_p16_const12'] = form.rating_const12.data
        session['rating_p16_const13'] = form.rating_const13.data
        session['rating_p16_const14'] = form.rating_const14.data
        session['rating_p16_const15'] = form.rating_const15.data
        # updating the database with the new batch of ratings (via a dictionary first)
        rating_fields = {'rating_p16_const1': form.rating_const1.data,
        'rating_p16_const2': form.rating_const2.data,
        'rating_p16_const3': form.rating_const3.data,
        'rating_p16_const4': form.rating_const4.data,
        'rating_p16_const5': form.rating_const5.data,
        'rating_p16_const6': form.rating_const6.data,
        'rating_p16_const7': form.rating_const7.data,
        'rating_p16_const8': form.rating_const8.data,
        'rating_p16_const9': form.rating_const9.data,
        'rating_p16_const10': form.rating_const10.data,
        'rating_p16_const11': form.rating_const11.data,
        'rating_p16_const12': form.rating_const12.data,
        'rating_p16_const13': form.rating_const13.data,
        'rating_p16_const14': form.rating_const14.data,
        'rating_p16_const15': form.rating_const15.data}
        db_session.query(SurveyData).filter_by(id=session['user_id']).update(rating_fields)
        db_session.commit()
        # Working out whether we have more ratings to do or not...
        return redirect(url_for('results'))
    return render_template('ratings.html', form=form, target=target,
        construct1pos_toshow = session.get('construct1pos'),
        construct1neg_toshow = session.get('construct1neg'),
        construct2pos_toshow = session.get('construct2pos'),
        construct2neg_toshow = session.get('construct2neg'),
        construct3pos_toshow = session.get('construct3pos'),
        construct3neg_toshow = session.get('construct3neg'),
        construct4pos_toshow = session.get('construct4pos'),
        construct4neg_toshow = session.get('construct4neg'),
        construct5pos_toshow = session.get('construct5pos'),
        construct5neg_toshow = session.get('construct5neg'),
        construct6pos_toshow = session.get('construct6pos'),
        construct6neg_toshow = session.get('construct6neg'),
        construct7pos_toshow = session.get('construct7pos'),
        construct7neg_toshow = session.get('construct7neg'),
        construct8pos_toshow = session.get('construct8pos'),
        construct8neg_toshow = session.get('construct8neg'),
        construct9pos_toshow = session.get('construct9pos'),
        construct9neg_toshow = session.get('construct9neg'),
        construct10pos_toshow = session.get('construct10pos'),
        construct10neg_toshow = session.get('construct10neg'),
        construct11pos_toshow = session.get('construct11pos'),
        construct11neg_toshow = session.get('construct11neg'),
        construct12pos_toshow = session.get('construct12pos'),
        construct12neg_toshow = session.get('construct12neg'),
        construct13pos_toshow = session.get('construct13pos'),
        construct13neg_toshow = session.get('construct13neg'),
        construct14pos_toshow = session.get('construct14pos'),
        construct14neg_toshow = session.get('construct14neg'),
        construct15pos_toshow = session.get('construct15pos'),
        construct15neg_toshow = session.get('construct15neg'),    )

###         else:
#            user_updated = db_session.query(SurveyData).order_by(SurveyData.id.desc()).first()
#            print(user_updated.rating_p15_const15)
#


################# Phase IV - Results ###########################
'''These are largely computed in another module and then imported here. I guess I make a dataframe to input into the function.
Then, have the function return a bunch of objects that I can display.'''
@app.route('/results', methods=['GET','POST'])
def results():
    # Get the right data bits
#    neg_hands = get_neg_handles()
#    pos_poles = get_pos_handles()
#    print(session)
#    const = get_construct_names()
#    targets = get_people_names()
    try:
        ratings_matrix = get_ratings_matrix()
        loadings_matrix = make_loadings_matrix(ratings_matrix) # Compute the loading matrix
        duplicates = ratings_matrix.duplicated()
        targets_matrix = make_targets_matrix(ratings_matrix, loadings_matrix)
        paragraph = loadings_describer(loadings_matrix, targets_matrix)
        loadings_map = draw_loadings_heatmap(loadings_matrix)
        targets_map = draw_targets_heatmap(targets_matrix)
        standings_chart = draw_standing_charts(targets_matrix)
        return render_template("results.html", paragraph=paragraph, loadings_map=loadings_map, targets_map=targets_map, standings_chart=standings_chart)
    except linalg.LinAlgError:
        ratings_matrix = get_ratings_matrix()
        return render_template("similar_people.html")
    except ValueError:
        ratings_matrix = get_ratings_matrix()
        print(ratings_matrix)
        return render_template("vague_ratings.html", tables=[ratings_matrix.to_html(classes='data')], titles=ratings_matrix.columns.values)
    else:
        return render_template("errors.html", tables=[ratings_matrix.to_html(classes='data')], titles=ratings_matrix.columns.values)
    # Run the correct functions from the results module

    # Then make the right results page (this is on the results.html template)
#    return render_template('results.html', tables=[targets_m.to_html(classes='data')], titles=targets_m.columns.values)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
    # Put the file cleanup in here

if __name__ == '__main__':
    app.run(debug=True)
