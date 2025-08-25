<template>
	<div class="report-page">
		<h1 class="title">报告管理</h1>
		<p class="description">这里是报告管理页面的内容。</p>

		<!-- 列表 -->
		<div class="report-list">
			<div class="report-item" v-for="(item, index) in reportData" :key="index">
				<div class="report-date">{{ formatDate(item.create_time) }}</div>
				<a @click.prevent="viewReport(item.content)" class="report-pdf">查看</a>
			</div>
		</div>

		<!-- 报告内容弹窗 -->
		<div v-if="showReportModal" class="modal">
			<div class="modal-content">
				<div class="close-buttons">
					<span class="close" @click="showReportModal = false">&times;</span>
					<div class="export-btn" @click="exportToPDF">导出</div>
				</div>
				<pre class="modal-text" ref="reportContent">{{ currentReport }}</pre>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { singleUserStore } from '@/utils/userStore';
import { useMessage } from 'naive-ui';
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
import { addfont } from '@/font/font'

const reportData = ref<any[]>([]);
const showReportModal = ref(false);
const currentReport = ref('');
const singleStore = singleUserStore();
const ms = useMessage();
const reportContent = ref<HTMLElement | null>(null);

// 获取报告数据
const fetchReportData = async () => {
	try {
		const userId = singleStore.getUserId();
		if (!userId) {
			console.error('用户 ID 为空，无法获取报告数据');
			ms.error('用户 ID 为空，无法获取报告数据');
			return;
		}
		const response = await axios.get(`http://127.0.0.1:5000/reports?user_id=${userId}`);
		reportData.value = response.data;
	} catch (error) {
		console.error('获取报告数据失败:', error);
		ms.error('获取报告数据失败');
	}
};

// 查看报告
const viewReport = (content: string) => {
	currentReport.value = content;
	showReportModal.value = true;
};

// 格式化日期
const formatDate = (dateStr: string) => {
	const date = new Date(dateStr);
	return new Intl.DateTimeFormat('zh-CN', {
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit'
	}).format(date);
};

// 导出 PDF
const exportToPDF = () => {

	const doc = new jsPDF();
	addfont(doc)
	// 添加字体
	doc.addFont('NotoSansSC-Light-normal.ttf', 'NotoSansSC-Light', 'normal');
	doc.setFont('NotoSansSC-Light');

	const text = currentReport.value;
	const maxWidth = 180; // 假设最大宽度为 180，可根据需要调整
	const lines = doc.splitTextToSize(text, maxWidth);
	doc.text(lines, 10, 10);

	doc.save('report.pdf');
};

// 页面加载时获取报告数据
onMounted(() => {
	fetchReportData();
});
</script>

<style scoped>
.report-page {
	padding: 20px;
	background-color: #121212;
	color: #f5f5f5;
	min-height: 100vh;
}

.title {
	font-size: 2rem;
	font-weight: 600;
	margin-bottom: 10px;
}

.description {
	font-size: 1.1rem;
	color: #b0b0b0;
	margin-bottom: 20px;
}

.report-list {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.report-item {
	display: flex;
	justify-content: space-between;
	padding: 10px;
	background-color: #2c2c2c;
	border-radius: 8px;
}

.report-date {
	font-size: 1rem;
}

.report-pdf {
	font-size: 1rem;
	color: #4caf50;
	text-decoration: none;
}

.report-pdf:hover {
	text-decoration: underline;
}

.modal {
	display: block;
	position: fixed;
	z-index: 1;
	left: 0;
	top: 0;
	width: 100%;
	height: 100%;
	overflow: auto;
	background-color: rgba(0, 0, 0, 0.4);
}

.modal-content {
	background-color: #2c2c2c;
	margin: 15% auto;
	padding: 20px;
	border: 1px solid #888;
	width: 80%;
	color: #f5f5f5;
	position: relative;
}

.close-buttons {
	position: absolute;
	top: 10px;
	right: 10px;
	display: flex;
	flex-direction: column;
}

.close {
	color: #aaa;
	font-size: 28px;
	font-weight: bold;
	cursor: pointer;
}

.close:hover,
.close:focus {
	color: black;
	text-decoration: none;
}

.export-btn {
	background-color: #4caf50;
	color: white;
	padding: 5px 10px;
	border-radius: 5px;
	cursor: pointer;
	margin-top: 5px;
}
.modal-text {
	color: #f5f5f5;
	white-space: pre-wrap;
	word-wrap: break-word;
}
</style>
