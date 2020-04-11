from sqlalchemy import text
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class TeamMember(db.Model):
	__tablename__ = 'teammembers'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(), nullable=False)
	duties = db.relationship('Duty', backref='member_in_charge', lazy=True)
	executions = db.relationship('Execution', backref='executer', lazy=True)
	is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
	###
	##id, name
	#.in_charge_of (Duty(s))
	#.executions (Executions - SELECT * FROM executions where member_id = self.if)
	###
	def __repr__(self):
		return '<TeamMember %r>' % self.name

	def delete(self):
		self.is_deleted = True
		db.session.commit()
		print(f'{self} Deleted')

#Default Queue - last execution time is earliest. if no executions - random order.
QUEUE_QUERY = """
SELECT t.id
  FROM teammembers t
  LEFT OUTER JOIN (
  		SELECT * 
  		  FROM executions
  		 WHERE duty_id = :duty_id) e
    ON(t.id = e.member_id)
 WHERE t.is_deleted = False
 GROUP BY t.id
 ORDER BY (CASE WHEN COUNT(e.execution_time) > 0 THEN 1 ELSE 0 END) ASC, MAX(e.execution_time) ASC, RANDOM()
 LIMIT 1;
"""
class Duty(db.Model):
	__tablename__ = 'duties'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(), nullable=False)
	description = db.Column(db.String(), nullable=True)
	last_execution = db.Column(db.DateTime(), nullable=True)
	queue_query = db.Column(db.String(), nullable=False, default=QUEUE_QUERY)
	is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
	member_id_in_charge = db.Column(db.Integer, db.ForeignKey('teammembers.id'), nullable=True)
	executions = db.relationship('Execution', backref='duty')
	###
	##id, name, description, last_execution, member_id_in_charge
	#.executions (Executions - SELECT * FROM executions where duty_id = self.id)
	###
	def __repr__(self):
		return '<Duty %r>' % self.name

	def delete(self):
		self.is_deleted = True
		self.member_id_in_charge = None
		db.session.commit()
		print(f'{self} Deleted')

	def executed(self):
		execution = Execution(member_id=self.member_id_in_charge, duty_id=self.id)
		self.last_execution = func.now()
		db.session.add(execution)
		db.session.commit()
		print (f'{self} {execution}')
		self.assign_next_in_queue()

	def set_queue_query(self, query):
		self.queue_query = query
		db.session.commit()

	def reset_queue_query(self):
		self.queue_query = QUEUE_QUERY
		db.session.commit()

	def get_next_in_queue(self):
		query = text(self.queue_query)
		params = {'duty_id': self.id}
		result = db.session.execute(query, params).fetchone()
		if result:
			member_id = result[0]
			return TeamMember.query.get(member_id)
		else:
			return None

	def assign_next_in_queue(self):
		member = self.get_next_in_queue()
		if member:
			self.member_id_in_charge = member.id
			print(f'{member.name} was assign to executed {self}')
		else:
			self.member_id_in_charge = None
			print(f'{self} is now unassigned')
		db.session.commit()

	def assign_member(self, member_id):
		self.member_id_in_charge = member_id
		db.session.commit()

class Execution(db.Model):
	__tablename__ = 'executions'
	id = db.Column(db.Integer, primary_key=True)
	member_id = db.Column(db.Integer, db.ForeignKey('teammembers.id'), nullable=False)
	duty_id = db.Column(db.Integer, db.ForeignKey('duties.id'), nullable=False)
	execution_time = db.Column(db.DateTime, server_default=func.now(), nullable=False)

	def __repr__(self):
		return '<Execution %r>' % self.execution_time