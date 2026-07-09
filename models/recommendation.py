"""Domänenmodell: Empfehlung – **vorbereitet, noch nicht Teil dieser Version**.

Dieses Modul ist der reservierte Ort für die künftigen, unveränderlichen
Empfehlungs-Datentypen (die erklärbare Zusammenführung aus Score, Muster und
Risiko). Alpha AI trifft **keine** automatischen Handelsentscheidungen und führt
keine Orders aus; eine Empfehlung ist ausschließlich eine nachvollziehbare,
erklärte Einschätzung. Eine Recommendation Engine existiert in dieser Version
bewusst **nicht** (siehe Roadmap); es werden hier daher noch keine Datentypen
definiert.

Grundsätze für die spätere Umsetzung (analog zu :mod:`models.score`):

* nur unveränderliche (``frozen``) Datenobjekte, keinerlei Logik;
* keine Importe aus höheren Schichten (Engines, Data, Dashboard).
"""

from __future__ import annotations
