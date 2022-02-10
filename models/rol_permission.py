from db import db


class RolPermissionModel(db.Model):
    __tablename__ = 'rol_permission'
    __table_args__ = {'schema': 'user'}

    id = db.Column(db.BigInteger, primary_key=True)
    rol_id = db.Column(db.BigInteger, db.ForeignKey('user.rol.id'))
    permission_id = db.Column(db.BigInteger, db.ForeignKey('user.permission.id'))
