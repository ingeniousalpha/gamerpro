# 📝 Technical requirements documentation

[Reference document](https://github.com/alexey-goloburdin/thanks/blob/main/docs/technical_requirements.md)
[Diagrams](https://drive.google.com/file/d/1Th1LN564w9wUunSoN-fxvyu_yomoJTjR/view?usp=sharing)

## 🚀 Goal of the project

To develop the system of sport event planning for any individual or organization interested in setting up their sport activity event. Sport event can be any tournament or competition activity between people or teams. Organizers can create and a sport event and participants will register to it, where organizer will have a dashboard with peoples registered to their sport event and can download clean excel table with registered people and distributed over their grading degree (classes / ages / weights and so on). Additionally system must be responsive with all entities organizers & participants linked by event sent notifications mechanisms (email and telegram). System will be entirely based on traditional web without any mobile app.

## ❤️‍🩹 Problem & Painpoint

Currently, there is no a software or platform that helps to find out about existing sport events and link participants with organizers.

1. Helps to people to find out about upcoming sport events in their area;
2. Helps organizers easier to manage communication with participants;
3. Helps to participants reduce complexity of registration to sport event;
4. Helps to easier organize events.

## ✍️ Description of the project

System is composed out of following functional blocks:

- Registration, authN & authZ
- Organizer's functionality
    - CRUD on event
- Partiticipant's functionality
    - Register to event
    - Refuse from participation
    - Update registration details
    - Subscription on upcoming events
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

- First name
- Last name
- Birth date
- Gender
- Contact details
    1. email (mandatory)
    2. phone number (mandatory)
    3. telegram (optional)
    4. whatsapp (optional)
- Password

### Registration fields :: organizer 🗄️

- Extends everything from participant
- Type: individual / organization
- About organizer

## 🔒 Authentification of users

Authentication is entirely done once off password provided over email or url?

## 👽 High-level functionality for differentt components

### **Guest**

- Read events
- Create user (participant / organizer)

### **Organizers**

- Create / Read / Update / Delete sport event
- Read participant card
- Analytics for event (?):
    - How many participants overall
    - How many participants under each category created

### **Participant**

- Read events
- Create / Read / Update / Delete participant card
- Create organizer (become own event organizer)

## **Notification**

- update / delete of sport event by organizer triggers notification process of registered participants using concact details provided in participant card.
- update / delete of participant card by participant triggers notification process of organizer using concact details provided by organizer ddd

## ⬛ Platform entities


### 🥇 Sport event

Some sport activity or tournament where people compete with each other in different sports such as team or inidividual based. Sport event details:

- Promo photo
- Event duration: start date & end date
- Registration deadlines (start date - end date)
- Location: where event will be performed
- About: Event details, promodetails or additional registration process details
- Contact details: Organizer contact details for communication
- Fee details: Participation fees
- Available categories: available competition categories or styles
- Participant / team parameters: parameters are provided by participant for organizational purposes
- Regulation documents: some documents that participants must to read & accept over website
- Schedule (can be added after registration ends): schedule of event
- Competition results (can be added after end of tournament)
