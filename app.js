const positionEl = document.getElementById("position");
const locationEl = document.getElementById("location");
const pagesEl = document.getElementById("pages");
const starterPageEl = document.getElementById("start");
const output = document.getElementById("output");
const errorDiv = document.querySelector('.error')


const fetchBtn = document.getElementById("fetch-data-button");
const deleteBtn = document.getElementById("delete-data-button")


async function fetchData() {


  const positionVal = positionEl.value.replace(" ", "+");
  const locationVal = locationEl.value.replace(" ", "+").replace(',', '%2C');
  const pagesVal = pagesEl.value;
  const starterPageVal = starterPageEl.value;
  const url = `https://7184e752-dd92-4f5e-abfc-82da0fa570f4.e1-eu-north-azure.choreoapps.dev/data?position=${positionVal}&location=${locationVal}&pages=${pagesVal}&start=${starterPageVal}`;

  try {
    const response = await fetch(url)

    if (!response.ok) {
      throw new error (`Network response was not ok: ${response.statusText}`);
    }
  }
  catch {
    document.querySelector('.loader').style.display = "none";
    errorDiv.innerHTML = "Data can't be fetched. Check that the server is running..."
  }

    const data = response.json()

      console.log(data);
      function tableHeaders() {
        let titleStr = "<thead> <tr> "
        const title = data.title //array of strings 
  
        for (let i=0; i <title.length; i++) {
           titleStr += `
           <th> ${title[i]} </th>
           `
        }

        titleStr += "</tr> </thead>"
        return titleStr
      }

      function tableData() {
        let jobsStr = "<tbody>"
        const jobs = data.jobs // array of arrays
        for (let i=0; i < jobs.length; i++) {
          jobsStr += "<tr>"
          for (let j=0; j < jobs[i].length; j++) {


            if (jobs[i].length === 6) {
              const linksIndex = jobs[i].length - 1

            if (j == linksIndex) {
              jobsStr += `
              <td> <a href=${jobs[i][j]}> Link </a> </td>
              `
            }
            else {
              jobsStr += `
              <td> ${jobs[i][j]} </td>
              `
            }
            }
            
          }
          jobsStr += "</tr>"
        }
        jobsStr += "</tbody>"
        return jobsStr
      } 

      const tableHeadersString = tableHeaders()
      const tableDataString = tableData()

      const tableString = tableHeadersString + tableDataString
      localStorage.setItem("data", tableString)
      output.innerHTML = tableString
     
      
      document.querySelector('.loader').style.display = "none";
  
}

const leadsFromLocalStorage = localStorage.getItem("data")

if (leadsFromLocalStorage) {
  output.innerHTML = leadsFromLocalStorage
}
fetchBtn.addEventListener("click", () => {

  if ((positionEl.value.trim() == "") || (locationEl.value.trim() == "" )|| (pagesEl.value.trim() == "") || (starterPageEl.value.trim() == "")) {
    
    errorDiv.innerHTML = "Please fill in all the input fields"
    return 
  }
  else {
    errorDiv.innerHTML = ""
  fetchData();
  document.querySelector('.loader').style.display = "block";
  positionEl.value = "";
  locationEl.value = "";
  pagesEl.value = "";
  starterPageEl.value = ""
  }
});

deleteBtn.addEventListener('dblclick', () => {
  output.innerHTML = ""
  localStorage.clear()
})
