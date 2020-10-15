### config.py ###

# For now, to test the database locally, you will have to set the URI below to log into your own database server of choice.
# TODO Uncomment the below with your own server's information.
# Scheme: "postgres+psycopg2://<USERNAME>:<PASSWORD>@<IP_ADDRESS>:<PORT>/<DATABASE_NAME>"

# DATABASE_URI = "postgres+psycopg2://<USERNAME>:<PASSWORD>@<IP_ADDRESS>:<PORT>/<DATABASE_NAME>"
DATABASE_URI = "postgres+psycopg2://postgres:bentopostgres@localhost:5432/megaqc1"