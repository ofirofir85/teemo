from flask import Flask, render_template, request, url_for, flash, redirect, session, jsonify
from flask_session import Session
from sqlalchemy import and_
from models import *
app = Flask(__name__)
app.secret_key = '12342sdfkm2##@&^sa12'

USERNAME = 'postgres'
PASSWORD = 'admin'
PORT = '5432'
DB_NAME = 'postgres'
HOSTNAME = 'localhost'
DB_TYPE = 'postgres'
app.config['SQLALCHEMY_DATABASE_URI'] = f'{DB_TYPE}://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
Session(app)

with app.app_context():
	db.create_all()

@app.route('/drop')
def drop():
	db.drop_all() 
	db.create_all()
	return redirect(url_for('logout'))

@app.route('/')
def home():
	if session.get('is_logged'):
		current_member = TeamMember.query.get(session['member_id'])
	else:
		current_member = TeamMember(name='Guest')
	return render_template('home.html', current_member=current_member)


@app.route('/get_members_data')
def get_members_data():
	members = TeamMember.query.filter_by(is_deleted = False).all()
	members_data = [{'id': member.id, 'name': member.name} for member in members]
	return jsonify(members_data)

@app.route('/login', methods=['POST'])
def login():
	member_id = request.form['user_select']
	if session.get('is_logged'):
		name = session['member_name']
		flash(f'you are already logged in as {name}', 'warning')
	else:
		member = TeamMember.query.filter(and_(TeamMember.id == member_id, TeamMember.is_deleted == False)).first()
		if member:
			session['member_id'] = member.id
			session['member_name'] = member.name
			session['is_logged'] = True
		else:
			flash('Error: Unvalid TeamMember ID','danger')
	return redirect(url_for('home'))

@app.route('/logout')
def logout():
	session['member_id'] = None
	session['member_name'] = None
	session['is_logged'] = False
	return redirect(url_for('home'))

@app.route('/duties')
def duties():
	duties = Duty.query.filter_by(is_deleted=False).all()
	teammembers = TeamMember.query.filter_by(is_deleted=False).all()
	return render_template('duties.html',teammembers=teammembers, duties=duties)

@app.route('/team')
def team():
	team_members = TeamMember.query.filter_by(is_deleted=False).all()
	return render_template('team.html', team_members=team_members)

@app.route('/add_member', methods=['POST'])
def add_member():
	name = request.form['name']
	team_member = TeamMember(name=name)
	db.session.add(team_member)
	db.session.commit()
	print(f'Added {team_member}')
	flash(f'{name} successfully added to team', 'success')
	return redirect(url_for('team'))

@app.route('/remove_member/<int:member_id>')
def remove_member(member_id):
	member = TeamMember.query.get(member_id)
	if member:
		member.delete()
		for duty in member.duties:
			duty.assign_next_in_queue()
		flash(f'{member.name} was deleted', 'success')
	else:
		flash(f'Error: {member_id} is an unvalid TeamMember.id', 'danger')
	
	if member_id == session['member_id']:
		logout()
	return redirect(url_for('team'))

@app.route('/remove_duty/<int:duty_id>')
def remove_duty(duty_id):
	duty = Duty.query.get(duty_id)
	if duty:
		duty.delete()
		flash(f'{duty.name} was deleted', 'success')
	else:
		flash(f'Error: {duty_id} -is an unvalid Duty.id','danger')
	return redirect(url_for('duties'))


@app.route('/add_duty', methods=['POST'])
def add_duty():
	name = request.form['name']
	description = request.form['description']
	assigned_member_id = int(request.form['assigned_member_id'])
	duty = Duty(name=name, description=description)
	db.session.add(duty)
	db.session.commit()
	if assigned_member_id == -1:
		duty.assign_next_in_queue()
	else:
		duty.member_id_in_charge = assigned_member_id
		db.session.commit()

	print(f'Added {duty}')
	flash(f'{name} successfully added to duties', 'success')
	return redirect(url_for('duties'))

@app.route('/execute/<int:duty_id>')
def execute_duty(duty_id):
	duty = Duty.query.get(duty_id)
	duty.executed()
	flash(f'{duty.name} successfully executed!', 'success')
	return redirect(url_for('home'))

@app.route('/change_duty/<int:duty_id>', methods=['POST'])
def change_duty(duty_id):
	member_id = int(request.form['assigned_member_id'])
	duty = Duty.query.get(duty_id)
	if member_id == -1:
		duty.assign_next_in_queue()
	else:
		duty.assign_member(member_id)
	flash('Changed Assignment Successfully', 'success')
	return redirect(url_for('duty', duty_id=duty_id))

@app.route('/duty_query/<int:duty_id>', methods=['POST'])
def duty_query(duty_id):
	duty = Duty.query.get(duty_id)
	submit = request.form['submit']
	if submit == 'default':
		duty.reset_queue_query()
		flash(f'{duty.name} queue query restored to default', 'success')
	elif submit == 'edit':
		query = request.form['query']
		duty.set_queue_query(query)
		flash(f'{duty.name} queue has been changed', 'success')
	return redirect(url_for('duty', duty_id=duty_id))

@app.route('/duty/<int:duty_id>')
def duty(duty_id):
	if session['is_logged'] == False:
		flash('You must be logged in to view duty', 'danger')
		return redirect(url_for('duties'))

	duty = Duty.query.filter(and_(Duty.id == duty_id, Duty.is_deleted == False)).first()
	if duty:
		return render_template('duty.html', duty=duty)
	else:
		flash('Error - Unvalid Duty ID','danger')
		return redirect(url_for('duties'))

