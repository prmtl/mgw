import peewee

# create not initialized db, it will be connected
# after reading config
database = peewee.SqliteDatabase(None)


def configure(conf):
    """Configure database connection"""
    database.init(conf['db_file'])


class UnknownField(object):

  def __init__(self, *args, **kwargs):
    pass


class BaseModel(peewee.Model):

  class Meta:
    database = database


class BoardDesc(BaseModel):
  board_desc = peewee.TextField(null=True)
  board = peewee.TextField(db_column='board_id', null=True, primary_key=True)

  class Meta:
    db_table = 'board_desc'


class LastMetrics(BaseModel):
  board = peewee.TextField(db_column='board_id', null=True)
  data = peewee.TextField(null=True)
  last_update = UnknownField()  # TIMESTAMP
  sensor_type = peewee.TextField(null=True)

  class Meta:
    db_table = 'last_metrics'


class Metrics(BaseModel):
  board = peewee.TextField(db_column='board_id', null=True)
  data = peewee.TextField(null=True)
  last_update = UnknownField()  # TIMESTAMP
  sensor_type = peewee.TextField(null=True)

  class Meta:
    db_table = 'metrics'
