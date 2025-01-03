import threading
import queue
import time

#Broker responsável por gerenciar filas e distribuição de mensagens
class Broker:
    def __init__(self):
        #Armazena filas de mensagens por tópico
        self.filas = {}  
        #Armazena filas de inscritos por tópico
        self.inscritos = {}  

    #Método de publicação das mensagens
    def divulgacao(self, message, topic):
        # Verifica se há inscritos para o tópico
        if topic in self.inscritos and self.inscritos[topic]:
            if topic not in self.filas:
                self.filas[topic] = queue.Queue()  #Cria fila para tópico se não existir
            self.filas[topic].put(message)  #Coloca a mensagem na fila do tópico
            self.notify_inscritos(topic)  #Notifica os inscritos no tópico
        else:
            print(f"Mensagem '{message}' descartada, pois não há assinantes para o tópico '{topic}'.")

    #Método de inscrição em tópicos
    def inscricao(self, subscriber, topic):
        if topic not in self.inscritos:
            self.inscritos[topic] = []
        self.inscritos[topic].append(subscriber)

    #Notifica os inscritos que há novas mensagens na fila do tópico
    def notify_inscritos(self, topic):
        if topic in self.filas and topic in self.inscritos:
            while not self.filas[topic].empty():
                message = self.filas[topic].get()
                for subscriber in self.inscritos[topic]:
                    subscriber.queue.put(message) #Coloca mensagem na fila do inscrito
                self.filas[topic].task_done()  #Marca a tarefa como completa

# Subscriber que recebe mensagens de tópicos via o broker
class Subscriber(threading.Thread):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.queue = queue.Queue()  # Fila para receber mensagens do broker
        self.daemon = True  # Para que a thread termine com o programa

    # Executa o loop de recebimento de mensagens
    def run(self):
        while True:
            message = self.queue.get()  #Aguarda e pega a próxima mensagem da fila
            print(f"{self.name} recebeu mensagem: {message}")
            self.queue.task_done()

#Publisher que envia mensagens para o broker
class Publisher(threading.Thread):
    def __init__(self, broker, name, messages, topic):
        super().__init__()
        self.broker = broker
        self.name = name
        self.messages = messages  #Lista de mensagens a serem enviadas
        self.topic = topic
        self.daemon = True  #Para que a thread termine com o programa

    #Envia as mensagens para o broker de forma assíncrona
    def run(self):
        for message in self.messages:
            print(f"{self.name} publicou: {message}")
            self.broker.divulgacao(message, self.topic)
            time.sleep(0.5)  #Simula tempo entre publicações


# Criando o broker
broker = Broker()

# Criando os inscritos (assinantes)
subscriber_1 = Subscriber("Assinante 1")
subscriber_2 = Subscriber("Assinante 2")
subscriber_3 = Subscriber("Assinante 3")
subscriber_4 = Subscriber("Assinante 4")

# Criando os publishers (publicadores) e publicando mensagens
publisher_1 = Publisher(broker, "Publicador A", ["Notícia de esportes 1", "Notícia de esportes 2"], "esportes")
publisher_2 = Publisher(broker, "Publicador B", ["Novo filme lançado"], "entretenimento")
publisher_3 = Publisher(broker, "Publicador C", ["Lançamento de novo smartphone"], "tecnologia")


# Início das threads dos inscritos
subscriber_1.start()
subscriber_2.start()
subscriber_3.start()
subscriber_4.start()

# Inscrição dos inscritos nos tópicos via broker
broker.inscricao(subscriber_1, "esportes")
broker.inscricao(subscriber_2, "entretenimento")
broker.inscricao(subscriber_3, "esportes")
broker.inscricao(subscriber_4, "entretenimento")

# Início das threads dos publishers
publisher_1.start()
publisher_2.start()
publisher_3.start()

# Espera para garantir que todas as mensagens sejam processadas
while True:
    time.sleep(3)

