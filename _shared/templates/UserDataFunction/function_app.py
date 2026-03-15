from fabric_user_data_functions import udf

@udf.function()
def hello():
    return "Hello"
