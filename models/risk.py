"""Domänenmodell: Risiko – **vorbereitet, noch nicht Teil dieser Version**.

Dieses Modul ist der reservierte Ort für die künftigen, unveränderlichen
Risiko-Datentypen (z. B. Positionsgröße, Stop-Abstand, Risiko-je-Trade). Eine
Risk Engine existiert in dieser Version bewusst **nicht** (siehe Roadmap); es
werden hier daher noch keine Datentypen definiert.

Grundsätze für die spätere Umsetzung (analog zu :mod:`models.score`):

* nur unveränderliche (``frozen``) Datenobjekte, keinerlei Logik;
* keine Importe aus höheren Schichten (Engines, Data, Dashboard).
"""

from __future__ import annotations
