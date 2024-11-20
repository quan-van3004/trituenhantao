import random
import pygal
from remi import gui
from remi import start, App
from io import BytesIO
import base64


class GeneticScheduler:
    def __init__(self, input_file, population_size=20, generations=100, mutation_rate=0.1):
        self.input_file = input_file
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.fitness_history = []  # Lưu trữ fitness tốt nhất qua các thế hệ

    def load_data(self):
        with open(self.input_file, "r", encoding="utf-8") as file:
            data = [line.strip().split(",") for line in file.readlines()]
        if len(data) < 2:
            raise ValueError("Dữ liệu đầu vào không đủ để tạo thời khóa biểu.")
        return data

    def create_individual(self, data):
        schedule = []
        time_slot = 7
        for i, (subject, teacher, _class) in enumerate(data):
            if time_slot >= 17:
                time_slot = 7
            time = f"Tiết {i+1}: {time_slot}h-{time_slot+1}h"
            schedule.append([time, _class, subject, teacher])
            time_slot += 1
        return schedule        

    def initialize_population(self, data):
        population = []
        for _ in range(self.population_size):
            random.shuffle(data)
            individual = self.create_individual(data)
            population.append(individual)
        return population

    def fitness(self, schedule):
        score = 0
        teacher_schedule = {}
        for entry in schedule:
            time, _class, subject, teacher = entry
            teacher_schedule.setdefault(teacher, []).append(time)

        for times in teacher_schedule.values():
            if len(times) > len(set(times)):  # Kiểm tra nếu giáo viên có lịch trùng
                score -= 10  

        return score

    def selection(self, population):
        sorted_population = sorted(population, key=self.fitness, reverse=True)
        selected_population = sorted_population[:max(2, len(sorted_population) // 2)]
        
        if len(selected_population) < 2:
            selected_population += sorted_population[:2]
        return selected_population    
    def crossover(self, parent1, parent2):
        crossover_point = random.randint(1, len(parent1) - 1)
        child = parent1[:crossover_point] + parent2[crossover_point:]
        return child

    def mutate(self, individual):
        if random.random() < self.mutation_rate:
            mutate_index = random.randint(0, len(individual) - 1)
            individual[mutate_index][1] += "X"  # Đột biến thay đổi lớp học
        return individual

    def run(self):
        data = self.load_data()
        population = self.initialize_population(data)

        for generation in range(self.generations):
            selected_population = self.selection(population)
            if len(selected_population) < 2:
                raise ValueError("Quần thể không đủ cá thể để thực hiện giao phối.")
            
            new_population = []
            for i in range(0, len(selected_population) - 1, 2):
                parent1, parent2 = selected_population[i], selected_population[i + 1]
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                new_population.append(child)

            population = new_population

            # Lưu fitness tốt nhất của thế hệ này
            best_fitness = max(self.fitness(ind) for ind in population)
            self.fitness_history.append(best_fitness)

        best_individual = max(population, key=self.fitness)
        return [["Thời Gian", "Lớp", "Môn", "Giáo Viên"]] + best_individual


class TimetableApp(App):
    def __init__(self, *args):
        super(TimetableApp, self).__init__(*args)

    def main(self):
        self.main_container = gui.VBox(width=800, height=600, style={'margin': 'auto', 'padding': '10px'})
        label = gui.Label("Quản lý thời khóa biểu", style={'font-size': '24px', 'font-weight': 'bold'})

        self.btn_input = gui.Button("Nhập Dữ Liệu", width=200, height=30)
        self.btn_input.onclick.connect(self.show_input)

        self.btn_generate = gui.Button("Tạo Thời Khóa Biểu", width=200, height=30)
        self.btn_generate.onclick.connect(self.generate_schedule)

        self.btn_show_chart = gui.Button("Hiển Thị Biểu Đồ Đánh Giá", width=200, height=30)
        self.btn_show_chart.onclick.connect(self.show_fitness_chart)

        self.table = gui.Table.new_from_list([["Thời Gian", "Lớp", "Môn", "Giáo Viên"]], width='100%')

        self.chart_container = gui.Image(width='100%', height='auto')

        self.main_container.append([label, self.btn_input, self.btn_generate, self.btn_show_chart, self.table, self.chart_container])
        return self.main_container

    def show_input(self, widget):
        input_window = gui.VBox(width=400, height=300, style={'margin': 'auto', 'padding': '10px', 'border': '1px solid black'})
        input_window.append(gui.Label("Nhập thông tin", style={'font-size': '18px', 'font-weight': 'bold', 'text-align': 'center'}))

        self.subject_input = gui.TextInput(single_line=True, hint="Nhập môn học", style={'width': '100%'})
        self.teacher_input = gui.TextInput(single_line=True, hint="Nhập giáo viên", style={'width': '100%'})
        self.class_input = gui.TextInput(single_line=True, hint="Nhập lớp học", style={'width': '100%'})

        save_button = gui.Button("Lưu", style={'margin-top': '10px'})
        save_button.onclick.connect(self.save_input_data)

        input_window.append([self.subject_input, self.teacher_input, self.class_input, save_button])
        self.main_container.append(input_window)

    def save_input_data(self, widget):
        subject = self.subject_input.get_value()
        teacher = self.teacher_input.get_value()
        _class = self.class_input.get_value()

        if not all([subject, teacher, _class]):
            self.main_container.append(gui.Label("Vui lòng nhập đầy đủ thông tin.", style={'color': 'red'}))
            return

        with open("input_data.txt", "a", encoding="utf-8") as file:
            file.write(f"{subject},{teacher},{_class}\n")

        self.main_container.append(gui.Label("Đã lưu dữ liệu thành công.", style={'color': 'green'}))

    def generate_schedule(self, widget):
        self.scheduler = GeneticScheduler("input_data.txt")
        try:
            schedule = self.scheduler.run()
            self.table.empty()
            self.table.append_from_list(schedule)
            self.main_container.append(gui.Label("Thời khóa biểu đã được tạo thành công.", style={'color': 'green'}))
        except ValueError as e:
            self.main_container.append(gui.Label(str(e), style={'color': 'red'}))

    def show_fitness_chart(self, widget):
        if not hasattr(self, 'scheduler') or not hasattr(self.scheduler, 'fitness_history') or not self.scheduler.fitness_history:
            self.main_container.append(gui.Label("Hãy tạo thời khóa biểu trước khi hiển thị biểu đồ.", style={'color': 'red'}))
            return

        # Tạo biểu đồ bằng Pygal
        chart = pygal.Line()
        chart.title = 'Biểu đồ Đánh Giá Fitness Qua Các Thế Hệ'
        chart.x_labels = [str(i) for i in range(1, len(self.scheduler.fitness_history) + 1)]
        chart.add('Fitness', self.scheduler.fitness_history)

        # Lưu biểu đồ vào buffer
        chart_data = chart.render()
        chart_data_base64 = base64.b64encode(chart_data).decode('utf-8')

        # Hiển thị biểu đồ trên giao diện
        self.chart_container.attributes['src'] = f"data:image/svg+xml;base64,{chart_data_base64}"
        self.main_container.append(self.chart_container)


if __name__ == "__main__":
    start(TimetableApp, address="0.0.0.0", port=8080)
