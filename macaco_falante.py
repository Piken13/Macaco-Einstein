import pyttsx3

# Acorda o robô
robo = pyttsx3.init()

# O que você quer que ele fale:
robo.say("Atenção humanos! O macaco aprendeu a programar e vai dominar o mundo!")

# Manda ele falar
robo.runAndWait()