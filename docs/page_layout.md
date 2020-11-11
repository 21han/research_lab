#Add a new .html file in the layout 

Layout.html is the root html file contains the header, Your html file would extends it with format:

```html
{% extends "layout.html" %}
{% block content %}
    <YOUR content>
{% endblock content %}
```
Put the new .html file in the templates folder
e.g. /home
```html
{% extends "layout.html" %}
{% block content %}
    <h1>Home Page</h1>
{% endblock content %}
```