{{- define "transport-twin.name" -}}{{ .Release.Name }}-transport-twin{{- end -}}
{{- define "transport-twin.labels" -}}
app.kubernetes.io/name: transport-twin
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- define "transport-twin.env" -}}
- name: TERAFLOW_URL
  value: {{ .Values.teraflow.url | quote }}
- name: TWIN_TOPOLOGY_SOURCE
  value: {{ .Values.twin.topologySource | quote }}
- name: TWIN_PORT
  value: {{ .Values.twin.port | quote }}
- name: NS3_TWIN_MODE
  value: {{ .Values.twin.ns3Mode | quote }}
- name: TWIN_SITE_PLAN
  value: /etc/twin/site_plan.json
{{- end -}}
{{- define "transport-twin.image" -}}{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}{{- end -}}
