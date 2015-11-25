import colander


Invalid = colander.Invalid


class RangedInt(colander.SchemaNode):
  schema_type = colander.Int
  missing = colander.required
  validator = colander.Range(min=0)


class RequiredString(colander.SchemaNode):
  schema_type = colander.String
  missing = colander.required


class SensorDataSchema(colander.MappingSchema):
  board_id = RequiredString()
  sensor_type = RequiredString()
  sensor_data = RequiredString()


class ExceptionsSchema(colander.SequenceSchema):
  board_id = RequiredString()


class ArmedCheckSchema(colander.MappingSchema):
  default = colander.SchemaNode(colander.Bool(),
                                missing=colander.required)

  except_ = ExceptionsSchema(missing=colander.required, name='except')


class ActionSchema(colander.MappingSchema):
  check_if_armed = ArmedCheckSchema()
  action_interval = RangedInt()
  threshold = RequiredString()
  message_template = RequiredString()
  fail_count = RangedInt()
  fail_interval = RangedInt()
  priority = RangedInt()
