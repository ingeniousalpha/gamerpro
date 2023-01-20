# 📝 Overview document

- [Reference document](https://github.com/alexey-goloburdin/thanks/blob/main/docs/technical_requirements.md)
- [Diagrams](https://drive.google.com/file/d/1Th1LN564w9wUunSoN-fxvyu_yomoJTjR/view?usp=sharing)
- [smoothcomp screenshot references](https://drive.google.com/drive/folders/1Edz4RWEObc1ZWkKgGzi5bneJEjbabF-P?usp=sharing)

## 🚀 Goal of the project

To develop sport event promotion system for any individual or organization interested in setting up their sport activity tournament. Sport tournament can be any tournament or competition activity between people or teams. Organizers can create and a sport tournament and participants will register to it, where organizer will have a dashboard with peoples registered to their sport tournament and can download clean excel table with registered people and distributed over their grading degree (classes / ages / weights and so on). Additionally system must be responsive with all entities organizers & participants linked by tournament sent notifications mechanisms (email and telegram). System will be entirely based on traditional web without any mobile app.

## ❤️‍🩹 Problem & Painpoint

Currently, there is no a software or platform that helps to find out about existing sport tournaments and link participants with organizers.

1. Helps to reach to community more easily
2. Helps organizers easier to manage organization of event & promotion
3. Helps participants easier to 
4. Helps to easier organize tournaments.

## ✍️ Description of the project

System is composed out of following functional blocks:

- Registration, authN & authZ
- Organizer's functionality
    - CRUD on tournament
- Partiticipant's functionality
    - Register to tournament
    - Refuse from participation
    - Update registration details
    - Subscription on upcoming tournaments
- Notification over email / telegram

## 👥 Types of users

System envisage following main types of users such as:

- Guest (No need for Login, AuthN & AuthZ)
- Organizer
- Participant
- Team
- Attendee (?)

Organier can be a participant, but participant can't be an organizer.

## 🫣 Registration

### Registration fields :: participant 🏃

- First name*
- Last name*
- Birth date*
- Gender*
- Contact details*
    1. email (mandatory)*
    2. phone number (mandatory)*
    3. telegram (optional)
    4. whatsapp (optional)
- Password

### Registration fields :: organizer 🗄️

- Extends everything from participant
- Type: organization
- Organization name: (if it is truly organization)

## 🔒 Authentification of users

Authentication is entirely done once off password provided over email or url?

## 👽 High-level functionality for differentt components

### **Guest**

- Read tournaments
- Create user (participant / organizer)

### **Organizers**

- Create / Read / Update / Delete sport tournament
- Read participant card
- Analytics for tournament (?):
    - How many participants overall
    - How many participants under each category created

### **Participant**

- Read tournaments
- Create / Read / Update / Delete participant card
- Create organizer (become own tournament organizer)
- Create / Read / Update / Delete team

## **Notification**

- update / delete of sport tournament by organizer triggers notification process of registered participants using concact details provided in participant card.
- update / delete of participant card by participant triggers notification process of organizer using concact details provided by organizer ddd
