STELLAR_CLASSIFICATION = (
    'O', 'B', 'A', 'F', 'G',
    'K', 'M', 'D', 'C', 'R',
    'W', 'N', 'S',
)

INT_CATALOGS = (
    'hr',
    'hd',
    'hip',
)

STR_CATALOGS = (
    'proper',
    'bf',
    'gl',
)

CATALOGS = STR_CATALOGS + INT_CATALOGS

POINT = (
    'ra', 'dec'
)

SPECT = 'spect'
CONSTELLATION = 'con'

OTHER_DATA = (
    'dist', 
    'mag', 
    'absmag',
)

LIST_OF_CONSTELLATIONS = (
    'and', 'ant', 'aps', 'aql', 'aqr', 'ara', 'ari', 'aur', 'boo', 'cae',
    'cam', 'cap', 'car', 'cas', 'cen', 'cep', 'cet', 'cha', 'cir', 'cma', 
    'cmi', 'cnc', 'col', 'com', 'cra', 'crb', 'crt', 'cru', 'crv', 'cvn', 
    'cyg', 'del', 'dor', 'dra', 'equ', 'eri', 'for', 'gem', 'gru', 'her', 
    'hor', 'hya', 'hyi', 'ind', 'lac', 'leo', 'lep', 'lib', 'lmi', 'lup', 
    'lyn', 'lyr', 'men', 'mic', 'mon', 'mus', 'nor', 'oct', 'oph', 'ori', 
    'pav', 'peg', 'per', 'phe', 'pic', 'psa', 'psc', 'pup', 'pyx', 'ret', 
    'scl', 'sco', 'sct', 'ser', 'sex', 'sge', 'sgr', 'tau', 'tel', 'tra', 
    'tri', 'tuc', 'uma', 'umi', 'vel', 'vir', 'vol', 'vul',
)

PATH_TO_HYGDATA_V3 = 'data/hygdata_v3.csv'

ERROR_IS_POINTS_RANGE_VALID = "'Dec' must be from -90 to 90, 'Ra' must be from -24 to 24!"
ERROR_CONSTELLATION_DOES_NOT_EXIST = "The constellation does not exist!"
ERROR_NOT_ENOUGH_POINTS = "Number of points must be greater than 2!"

REDIS_SETTINGS = {
    "host": "redis",
    "port": 6379,
    "encoding": "utf-8",
    "decode_responses": True,
}

POSTGRESQL_SETTINGS = {
    "POSTGRES_DB": "star",
    "POSTGRES_USER": "admin",
    "POSTGRES_PASSWORD": "password",
}

PAGINATION_SIZE = 10
SERVER = '127.0.0.1'
PORT = 5000
SERVER_URL = SERVER + ":" + str(PORT)
