from pyexistdb import db

connection = db.ExistDB("http://localhost:8080/exist/", username="admin", password="")
connection.createCollection("gimnasio", overwrite=True)
connection.load(open("data/actividades_gim.xml"), "/gimnasio/actividades_gim.xml")
connection.load(open("data/socios_gim.xml"), "/gimnasio/socios_gim.xml")
connection.load(open("data/uso_gimnasio.xml"), "/gimnasio/uso_gimnasio.xml")


def preparar_intermedio():
    print("Creando fichero intermedio...")
    query: str = open("data/query_intermedia", "r").read()
    q = connection.executeQuery(query)
    result: str = "<result>"
    for i in range(connection.getHits(q)):
        result += str(connection.retrieve(q, i))
    result += "</result>"
    connection.load(result, "/gimnasio/intermedia.xml")


def borrar_intermedio():
    print("Borrando fichero intermedio...")
    connection.removeDocument("/gimnasio/intermedia.xml")


def codigos_de_socios() -> list:
    print("Obteniendo los codigos de socios...")
    codigos = []
    query = """for $socio in doc("/gimnasio/socios_gim.xml")//fila_socios/COD
    return $socio/text()"""
    q = connection.executeQuery(query)
    for i in range(connection.getHits(q)):
        codigos.append(str(connection.retrieve(q, i)))

    return codigos


def calcular_tasa_socios():
    preparar_intermedio()
    cuotas_socios: list = []
    plantilla_resultado = """<datos>
    <COD>{}</COD>
    <NOMBRESOCIO>{}</NOMBRESOCIO>
    <CUOTA_FIJA>{}</CUOTA_FIJA>
    <suma_cuota_adic>{}</suma_cuota_adic>
    <cuota_total>{}</cuota_total>
</datos>"""
    print("Calculando las tasas de los socios...")
    for codigo_socio in codigos_de_socios():
        print("Calculando la tasa de", nombre_de_codigo(codigo_socio))
        cuota_fija: float = cuota_fija_socio(codigo_socio)
        cuota_no_fija: float = cuotas_no_fijas_socios(codigo_socio)
        resultado: str = plantilla_resultado.format(codigo_socio, nombre_de_codigo(codigo_socio),
                                                    cuota_fija, cuota_no_fija, cuota_fija + cuota_no_fija)
        cuotas_socios.append(resultado)
    borrar_intermedio()
    return cuotas_socios


def nombre_de_codigo(socio: int) -> str:
    query = """for $socio in doc("/gimnasio/socios_gim.xml")//fila_socios[COD = {}]
    return $socio/NOMBRE/text()""".format(socio)
    q = connection.executeQuery(query)
    cuota: str = ""
    for i in range(connection.getHits(q)):
        cuota = str(connection.retrieve(q, i))
    return cuota


def cuotas_no_fijas_socios(socio: int) -> float:
    query = """for $socio in doc("/gimnasio/intermedia.xml")//datos[COD = {}]
    return $socio/cuota_adicional/text()""".format(socio)
    q = connection.executeQuery(query)
    cuota: float = 0
    for i in range(connection.getHits(q)):
        cuota += int(str(connection.retrieve(q, i)))
    return cuota


def cuota_fija_socio(socio: int) -> int:
    query = """for $socio in doc("/gimnasio/socios_gim.xml")//fila_socios[COD={}]
return $socio/CUOTA_FIJA/text()""".format(socio)
    q = connection.executeQuery(query)
    cuota: int = 0
    for i in range(connection.getHits(q)):
        cuota = int(str(connection.retrieve(q, i)))
    return cuota


def subir_cuotas() -> None:
    cuotas: str = "<resultado>"
    for cuota in calcular_tasa_socios():
        cuotas += "\n" + cuota
    cuotas += "</resultado>"
    connection.load(cuotas, "/gimnasio/resultado.xml")
    print("Resultados subidos.")
