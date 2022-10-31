helm repo add bitnami https://charts.bitnami.com/bitnami
helm install my-release bitnami/kafka
# Read more about the installation in the Apache Kafka packaged by Bitnami Chart Github repository

helm install kafka -f apache-kafka/values.yaml  bitnami/kafka -n dev1

To set up size of empty dir (a temporary directory that shares a pod's lifetime) you need to limit the size of emptyDir in configmap.
For example kubectl edit statefulset.apps/kafka2:

      volumes:
      - configMap:
          defaultMode: 493
          name: kafka2-scripts
        name: scripts
      - emptyDir:
          sizeLimit: 900m
        name: data
      - emptyDir:
          sizeLimit: 900m
        name: logs


Kafka can be accessed by consumers via port 9092 on the following DNS name from within your cluster:

    kafka.dev1.svc.cluster.local

Each Kafka broker can be accessed by producers via port 9092 on the following DNS name(s) from within your cluster:

    kafka-0.kafka-headless.dev1.svc.cluster.local:9092

To create a pod that you can use as a Kafka client run the following commands:

    kubectl run kafka-client --restart='Never' --image docker.io/bitnami/kafka:3.1.0-debian-10-r0 --namespace dev1 --command -- sleep infinity
    kubectl exec --tty -i kafka-client --namespace dev1 -- bash

    PRODUCER:
        kafka-console-producer.sh \

            --broker-list kafka-0.kafka-headless.dev1.svc.cluster.local:9092 \
            --topic test

    CONSUMER:
        kafka-console-consumer.sh \

            --bootstrap-server kafka.dev1.svc.cluster.local:9092 \
            --topic test \
            --from-beginning
