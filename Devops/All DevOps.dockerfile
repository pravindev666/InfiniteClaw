FROM amazonlinux:latest
MAINTAINER mathew
RUN yum update -y && yum install -y vim wget
RUN yum install -y git
RUN yum install java -y
RUN wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
RUN rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io.key
RUN yum install -y jenkins
RUN amazon-linux-extras install ansible2 -y
RUN yum install -y yum-utils
RUN yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
RUN yum install -y terraform
RUN wget -O splunk.rpm 'https://download.splunk.com/products/splunk/releases/8.2.3/linux/splunk-8.2.3-87e2d4b0e9ce-linux-2.6-x86_64.rpm'
RUN rpm -i splunk.rpm
RUN rm splunk.rpm
RUN wget -O /tmp/prometheus.tar.gz https://github.com/prometheus/prometheus/releases/download/v2.26.0/prometheus-2.26.0.linux-amd64.tar.gz
RUN mkdir -p /etc/prometheus && tar -xvf /tmp/prometheus.tar.gz -C /etc/prometheus --strip-components=1
RUN ln -s /etc/prometheus/prometheus /usr/local/bin/prometheus
RUN yum install -y https://repo.saltproject.io/yum/amazon/salt-amzn-repo-latest-2.amzn2.noarch.rpm
RUN yum install -y salt-master salt-minion
RUN yum clean all
EXPOSE 8080 9090
# Start services (example, you need an appropriate entrypoint or CMD to start all services)
CMD ["jenkins"]