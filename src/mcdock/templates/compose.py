from jinja2 import Template

COMPOSE_TEMPLATE: Template = Template(
    """
services:
  mc-server:
    image: {{ image }}
    container_name: {{ name }}
    restart: unless-stopped
    environment:
      EULA: "{{ 'TRUE' if eula else 'FALSE' }}"
      MEMORY: "{{ memory }}"
{%- for var in env %}
      {{ var.key }}: "{{ var.value }}"
{%- endfor %}
    ports:
{%- for p in ports %}
      - "{{ p.host_port }}:{{ p.container_port }}/{{ p.type.value }}"
{%- endfor %}
    volumes:
      - ./data:/data
""",
    lstrip_blocks=True,
)